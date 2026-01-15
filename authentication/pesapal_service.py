"""
Pesapal API 3.0 Integration Service
Handles payment initialization, verification, and recurring payments
"""

import requests
import logging
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Payment, UserSubscription
from django.contrib.auth.models import User

logger = logging.getLogger('pesapal')

# In-memory token cache (consider Redis for production)
_token_cache = {
    'token': None,
    'expires_at': None
}


def get_access_token():
    """
    Get OAuth access token from Pesapal
    Implements caching to avoid unnecessary API calls
    """
    # Check if cached token is still valid
    if _token_cache['token'] and _token_cache['expires_at']:
        if timezone.now() < _token_cache['expires_at']:
            return _token_cache['token']

    # Request new token
    url = f"{settings.PESAPAL_BASE_URL}/Auth/RequestToken"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    payload = {
        'consumer_key': settings.PESAPAL_CONSUMER_KEY,
        'consumer_secret': settings.PESAPAL_CONSUMER_SECRET
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()
        token = data.get('token')

        if token:
            # Cache token for 5 minutes (tokens typically last longer)
            _token_cache['token'] = token
            _token_cache['expires_at'] = timezone.now() + timedelta(minutes=5)
            logger.info("Pesapal access token obtained successfully")
            return token
        else:
            logger.error(f"Failed to get access token: {data}")
            raise Exception("No token in response")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error requesting Pesapal token: {str(e)}")
        raise Exception(f"Failed to get Pesapal access token: {str(e)}")


def map_period_to_pesapal_frequency(period):
    """
    Map subscription plan period to Pesapal frequency
    """
    mapping = {
        'daily': 'DAILY',
        'weekly': 'WEEKLY',
        'monthly': 'MONTHLY',
        'yearly': 'YEARLY',
        'quarterly': 'MONTHLY'  # Quarterly mapped to monthly (user configures 3 months)
    }
    return mapping.get(period, 'MONTHLY')


def initialize_payment(user, plan, subscription, payment):
    """
    Initialize payment with Pesapal
    Creates order request with recurring payment support

    Args:
        user: User object
        plan: SubscriptionPlan object
        subscription: UserSubscription object
        payment: Payment object (already created)

    Returns:
        dict: {
            'order_tracking_id': str,
            'redirect_url': str,
            'merchant_reference': str
        }
    """
    token = get_access_token()

    url = f"{settings.PESAPAL_BASE_URL}/Transactions/SubmitOrderRequest"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    # Calculate subscription dates
    start_date = timezone.now()
    end_date = start_date + timedelta(days=plan.get_duration_in_days())

    # Build billing address
    billing_address = {
        'email_address': user.email,
        'phone_number': '',  # Optional
        'country_code': 'KE',  # Default to Kenya
        'first_name': user.first_name or user.username,
        'middle_name': '',
        'last_name': user.last_name or '',
        'line_1': '',  # Optional
        'line_2': '',
        'city': '',
        'state': '',
        'postal_code': '',
        'zip_code': ''
    }

    # Payment request payload
    payload = {
        'id': payment.pesapal_merchant_reference,
        'currency': payment.currency,
        'amount': float(payment.amount),
        'description': f'Subscription to {plan.name} - {plan.period_count} {plan.period}',
        'callback_url': settings.PESAPAL_CALLBACK_URL,
        'notification_id': settings.PESAPAL_IPN_ID,
        'billing_address': billing_address,
        'account_number': payment.pesapal_merchant_reference,  # Enables recurring opt-in
        'subscription_details': {
            'start_date': start_date.strftime('%d-%m-%Y'),
            'end_date': end_date.strftime('%d-%m-%Y'),
            'frequency': map_period_to_pesapal_frequency(plan.period)
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()

        order_tracking_id = data.get('order_tracking_id')
        redirect_url = data.get('redirect_url')

        if not order_tracking_id or not redirect_url:
            logger.error(f"Invalid response from Pesapal: {data}")
            raise Exception("Invalid response from Pesapal")

        logger.info(f"Payment initialized for user {user.id}: {order_tracking_id}")

        return {
            'order_tracking_id': order_tracking_id,
            'redirect_url': redirect_url,
            'merchant_reference': payment.pesapal_merchant_reference
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error initializing payment: {str(e)}")
        if hasattr(e.response, 'text'):
            logger.error(f"Response: {e.response.text}")
        raise Exception(f"Failed to initialize payment: {str(e)}")


def verify_payment(order_tracking_id):
    """
    Verify payment status with Pesapal

    Args:
        order_tracking_id: Pesapal OrderTrackingId

    Returns:
        dict: Transaction data from Pesapal
    """
    token = get_access_token()

    url = f"{settings.PESAPAL_BASE_URL}/Transactions/GetTransactionStatus"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    params = {
        'orderTrackingId': order_tracking_id
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()

        data = response.json()

        logger.info(f"Payment verification for {order_tracking_id}: {data.get('payment_status_description')}")

        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"Error verifying payment: {str(e)}")
        if hasattr(e.response, 'text'):
            logger.error(f"Response: {e.response.text}")
        raise Exception(f"Failed to verify payment: {str(e)}")


def process_ipn_notification(order_tracking_id):
    """
    Process IPN notification from Pesapal
    Handles both initial payments and recurring renewals

    Args:
        order_tracking_id: Pesapal OrderTrackingId from IPN

    Returns:
        dict: {'success': bool, 'message': str}
    """
    try:
        # Verify payment status with Pesapal
        transaction_data = verify_payment(order_tracking_id)

        payment_status = transaction_data.get('payment_status_description', '')

        # Try to find existing payment record
        try:
            payment = Payment.objects.get(pesapal_order_tracking_id=order_tracking_id)

            if payment_status == 'Completed' and payment.status != 'successful':
                # Update payment
                payment.status = 'successful'
                payment.pesapal_transaction_id = transaction_data.get('confirmation_code', '')
                payment.payment_method = transaction_data.get('payment_method', '')
                payment.metadata = transaction_data
                payment.save()

                logger.info(f"Payment {payment.id} marked as successful")

                # Activate or extend subscription
                subscription = payment.subscription

                if payment.payment_type == 'subscription':
                    # Initial payment - activate subscription
                    subscription.activate_subscription()

                    if payment.is_recurring:
                        subscription.recurring_payment_active = True
                        subscription.save()

                    logger.info(f"Subscription {subscription.id} activated")

                elif payment.payment_type == 'renewal':
                    # Recurring renewal - extend subscription
                    subscription.start_date = timezone.now()
                    subscription.end_date = timezone.now() + timedelta(days=subscription.plan.get_duration_in_days())
                    subscription.status = 'active'
                    subscription.last_recurring_payment_date = timezone.now()
                    subscription.save()

                    logger.info(f"Subscription {subscription.id} renewed via recurring payment")

            elif payment_status == 'Failed':
                payment.status = 'failed'
                payment.metadata = transaction_data
                payment.save()

                logger.warning(f"Payment {payment.id} failed")

            return {'success': True, 'message': 'IPN processed successfully'}

        except Payment.DoesNotExist:
            # This might be a new recurring payment initiated by Pesapal
            merchant_reference = transaction_data.get('merchant_reference', '')

            if not merchant_reference:
                logger.error(f"No payment found for {order_tracking_id} and no merchant reference")
                return {'success': False, 'message': 'Payment not found'}

            # Extract user_id from merchant reference (format: SUB-{user_id}-xxx)
            try:
                parts = merchant_reference.split('-')
                if len(parts) >= 2 and parts[0] == 'SUB':
                    user_id = int(parts[1])
                    user = User.objects.get(id=user_id)
                    subscription = UserSubscription.objects.get(user=user)

                    # Create new renewal payment record
                    if payment_status == 'Completed':
                        payment = Payment.objects.create(
                            user=user,
                            subscription=subscription,
                            plan=subscription.plan,
                            amount=transaction_data.get('amount', subscription.plan.amount),
                            payment_type='renewal',
                            status='successful',
                            pesapal_order_tracking_id=order_tracking_id,
                            pesapal_merchant_reference=merchant_reference,
                            pesapal_transaction_id=transaction_data.get('confirmation_code', ''),
                            payment_method=transaction_data.get('payment_method', ''),
                            currency=transaction_data.get('currency', settings.PESAPAL_CURRENCY),
                            is_recurring=True,
                            metadata=transaction_data
                        )

                        # Extend subscription
                        subscription.start_date = timezone.now()
                        subscription.end_date = timezone.now() + timedelta(days=subscription.plan.get_duration_in_days())
                        subscription.status = 'active'
                        subscription.last_recurring_payment_date = timezone.now()
                        subscription.save()

                        logger.info(f"New recurring payment created for subscription {subscription.id}")

                        return {'success': True, 'message': 'Recurring payment processed', 'renewal': True}

                logger.error(f"Invalid merchant reference format: {merchant_reference}")
                return {'success': False, 'message': 'Invalid merchant reference'}

            except (ValueError, User.DoesNotExist, UserSubscription.DoesNotExist) as e:
                logger.error(f"Error processing recurring payment: {str(e)}")
                return {'success': False, 'message': str(e)}

    except Exception as e:
        logger.error(f"Error processing IPN notification: {str(e)}")
        return {'success': False, 'message': str(e)}


def register_ipn_url(ipn_url, ipn_notification_type='GET'):
    """
    Register IPN URL with Pesapal (one-time setup)

    Args:
        ipn_url: Full URL for IPN notifications (must be HTTPS in production)
        ipn_notification_type: 'GET' or 'POST' (Pesapal uses GET)

    Returns:
        str: IPN ID to be stored in settings
    """
    token = get_access_token()

    url = f"{settings.PESAPAL_BASE_URL}/URLSetup/RegisterIPN"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    payload = {
        'url': ipn_url,
        'ipn_notification_type': ipn_notification_type
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()
        ipn_id = data.get('ipn_id')

        if ipn_id:
            logger.info(f"IPN URL registered successfully: {ipn_id}")
            return ipn_id
        else:
            logger.error(f"Failed to register IPN URL: {data}")
            raise Exception("No IPN ID in response")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error registering IPN URL: {str(e)}")
        if hasattr(e.response, 'text'):
            logger.error(f"Response: {e.response.text}")
        raise Exception(f"Failed to register IPN URL: {str(e)}")
