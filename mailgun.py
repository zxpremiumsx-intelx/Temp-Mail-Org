"""
Mailgun API Integration
Handles email creation and deletion via Mailgun routes
"""

import os
import logging
import secrets
import string
import requests
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Mailgun configuration from environment
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_API_BASE = "https://api.mailgun.net/v3"

# Webhook URL for incoming mail (optional, for future implementation)
WEBHOOK_URL = os.getenv("MAILGUN_WEBHOOK_URL", "")


class MailgunError(Exception):
    """Custom exception for Mailgun API errors."""
    pass


def validate_config() -> bool:
    """
    Validate that required Mailgun configuration is present.
    Returns True if valid, raises exception if not.
    """
    if not MAILGUN_API_KEY:
        raise MailgunError("MAILGUN_API_KEY environment variable is required")
    if not MAILGUN_DOMAIN:
        raise MailgunError("MAILGUN_DOMAIN environment variable is required")
    return True


def generate_random_local_part(length: int = 12) -> str:
    """
    Generate a random local part for email address.
    Uses lowercase letters and numbers for compatibility.
    """
    chars = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def create_email() -> Tuple[str, Optional[str]]:
    """
    Create a new temporary email address.
    
    Returns:
        Tuple of (email_address, route_id)
        route_id is None if route creation is skipped
    
    Raises:
        MailgunError: If API call fails
    """
    validate_config()
    
    # Generate unique email address
    local_part = generate_random_local_part()
    email_address = f"{local_part}@{MAILGUN_DOMAIN}"
    
    # Create a route for incoming mail (optional)
    route_id = None
    if WEBHOOK_URL:
        try:
            route_id = create_mail_route(email_address)
        except MailgunError as e:
            logger.warning(f"Failed to create mail route: {e}")
            # Continue without route - email can still receive mail
    
    logger.info(f"Created email: {email_address}")
    return email_address, route_id


def create_mail_route(email_address: str) -> str:
    """
    Create a Mailgun route for forwarding incoming mail.
    
    Args:
        email_address: The email address to create route for
    
    Returns:
        The route ID from Mailgun
    
    Raises:
        MailgunError: If API call fails
    """
    validate_config()
    
    url = f"{MAILGUN_API_BASE}/routes"
    
    # Route expression to match this specific email
    expression = f'match_recipient("{email_address}")'
    
    # Action to forward to webhook
    action = f'forward("{WEBHOOK_URL}")'
    
    data = {
        "priority": 0,
        "description": f"Temp mail route for {email_address}",
        "expression": expression,
        "action": [action, "stop()"]
    }
    
    response = requests.post(
        url,
        auth=("api", MAILGUN_API_KEY),
        data=data,
        timeout=30
    )
    
    if response.status_code != 200:
        logger.error(f"Mailgun route creation failed: {response.text}")
        raise MailgunError(f"Failed to create mail route: {response.status_code}")
    
    route_data = response.json()
    route_id = route_data.get("route", {}).get("id")
    
    logger.info(f"Created mail route: {route_id} for {email_address}")
    return route_id


def delete_email(email_address: str) -> bool:
    """
    Delete an email from Mailgun by removing its route.
    
    Note: Mailgun doesn't have a concept of "deleting" an email address.
    We delete the associated route to stop receiving mail.
    
    Args:
        email_address: The email address to delete
    
    Returns:
        True if deletion was successful or no route exists
    
    Raises:
        MailgunError: If API call fails
    """
    validate_config()
    
    # Find and delete routes matching this email
    try:
        routes = get_routes_for_email(email_address)
        
        for route in routes:
            route_id = route.get("id")
            if route_id:
                delete_route(route_id)
        
        logger.info(f"Deleted email: {email_address}")
        return True
        
    except MailgunError as e:
        logger.error(f"Failed to delete email {email_address}: {e}")
        raise


def get_routes_for_email(email_address: str) -> list:
    """
    Get all Mailgun routes associated with an email address.
    
    Args:
        email_address: Email to search routes for
    
    Returns:
        List of route dictionaries
    """
    validate_config()
    
    url = f"{MAILGUN_API_BASE}/routes"
    
    response = requests.get(
        url,
        auth=("api", MAILGUN_API_KEY),
        params={"limit": 100},
        timeout=30
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch routes: {response.text}")
        raise MailgunError(f"Failed to fetch routes: {response.status_code}")
    
    all_routes = response.json().get("items", [])
    
    # Filter routes matching this email
    matching_routes = []
    for route in all_routes:
        expression = route.get("expression", "")
        if email_address in expression:
            matching_routes.append(route)
    
    return matching_routes


def delete_route(route_id: str) -> bool:
    """
    Delete a specific Mailgun route.
    
    Args:
        route_id: The Mailgun route ID to delete
    
    Returns:
        True if successful
    
    Raises:
        MailgunError: If API call fails
    """
    validate_config()
    
    url = f"{MAILGUN_API_BASE}/routes/{route_id}"
    
    response = requests.delete(
        url,
        auth=("api", MAILGUN_API_KEY),
        timeout=30
    )
    
    if response.status_code not in [200, 404]:
        logger.error(f"Failed to delete route {route_id}: {response.text}")
        raise MailgunError(f"Failed to delete route: {response.status_code}")
    
    logger.info(f"Deleted route: {route_id}")
    return True


def verify_domain() -> bool:
    """
    Verify that the Mailgun domain is properly configured.
    Useful for startup checks.
    
    Returns:
        True if domain is verified and active
    """
    validate_config()
    
    url = f"{MAILGUN_API_BASE}/domains/{MAILGUN_DOMAIN}"
    
    try:
        response = requests.get(
            url,
            auth=("api", MAILGUN_API_KEY),
            timeout=30
        )
        
        if response.status_code == 200:
            domain_data = response.json().get("domain", {})
            state = domain_data.get("state")
            logger.info(f"Domain {MAILGUN_DOMAIN} state: {state}")
            return state == "active"
        else:
            logger.warning(f"Domain verification failed: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"Domain verification error: {e}")
        return False

