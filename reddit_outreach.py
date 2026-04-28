#!/usr/bin/env python3
"""Reddit DM outreach script using Playwright browser automation."""

import json
import time
import random
import sys
from playwright.sync_api import sync_playwright

SESSION_FILE = "/home/keithbo/.openclaw/workspace/local_dashboard/data/sessions/reddit_session_affectionate.json"

SUBJECT = "Promo opportunity — 40K subscriber subreddit"

MESSAGE = """Hey! I run r/chibigbootygirls on Reddit — 40,000 subscribers, all into thick and curvy content.

I saw your post about needing help with promotion and I think I can help. I promote creators through my sub — regular features, engagement, consistent traffic to your page. No cost, we just split what my traffic brings in.

40K is a lot of eyeballs looking for exactly your type of content. Want to try a feature this week and see what happens?"""

# Skip list - non-fits
SKIP = {
    "NeighborhoodBoyJay", "bumpthebass", "Former-Nature4051", "bladee-enjoyer",
    "urine4atreat_", "martufindom", "nicocruz1", "prohibitedsteps",
    "Murky_Resolution_600", "Nervous_Worldliness9", "Accurate-Medicine560",
    "tcdstorm1", "JesusisLord2003", "Ok-Temperature-9529", "Nikki_Cole940",
    "Intrepid-Cloud2865"
}

# Target creators - everyone else from the advice subs who need promo help
# These are creators posting in r/OnlyFansAdvice, r/CreatorsAdvice, r/fansly_advice
# asking about promotion, traffic, marketing, growing their page
TARGETS = []

def load_cookies():
    with open(SESSION_FILE) as f:
        data = json.load(f)
    return data.get("cookies", [])

def try_old_reddit_message(page, username, results):
    """Try sending via old.reddit.com message compose (most reliable)."""
    url = f"https://old.reddit.com/message/compose/?to={username}"
    print(f"  Trying old.reddit.com compose for u/{username}...")
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    time.sleep(2)

    # Check if we're logged in
    page_text = page.content()
    if "login" in page.url.lower() and "compose" not in page.url.lower():
        print(f"  ERROR: Not logged in, redirected to login page")
        return "login_failed"

    # Check for error messages (user doesn't accept messages, etc.)
    if "that user doesn't exist" in page_text.lower() or "page not found" in page_text.lower():
        print(f"  ERROR: User u/{username} doesn't exist or page not found")
        return "user_not_found"

    # Fill subject
    try:
        subject_field = page.locator('input[name="subject"]')
        if subject_field.count() > 0:
            subject_field.fill(SUBJECT)
            time.sleep(0.5)
        else:
            print(f"  No subject field found on old reddit")
            return "no_form"
    except Exception as e:
        print(f"  Error filling subject: {e}")
        return "no_form"

    # Fill message body
    try:
        message_field = page.locator('textarea[name="message"]')
        if message_field.count() > 0:
            message_field.fill(MESSAGE)
            time.sleep(0.5)
        else:
            print(f"  No message textarea found")
            return "no_form"
    except Exception as e:
        print(f"  Error filling message: {e}")
        return "no_form"

    # Click send
    try:
        send_btn = page.locator('button[type="submit"]').first
        if send_btn.count() == 0:
            send_btn = page.locator('button:has-text("send")').first
        if send_btn.count() == 0:
            send_btn = page.locator('input[type="submit"]').first

        send_btn.click()
        time.sleep(3)

        # Check for success or errors
        page_text = page.content().lower()
        if "your message has been delivered" in page_text:
            print(f"  SUCCESS: Message sent to u/{username}")
            return "sent"
        elif "you are doing that too much" in page_text or "rate limit" in page_text or "try again" in page_text:
            print(f"  RATE LIMITED sending to u/{username}")
            return "rate_limited"
        elif "that user has blocked you" in page_text or "blocked" in page_text:
            print(f"  BLOCKED by u/{username}")
            return "blocked"
        elif "doesn't accept" in page_text:
            print(f"  User u/{username} doesn't accept messages")
            return "no_dms"
        else:
            # Check if URL changed to sent messages
            if "/message/sent" in page.url or "your message has been" in page_text:
                print(f"  SUCCESS (URL redirect): Message sent to u/{username}")
                return "sent"
            print(f"  UNKNOWN result for u/{username}, checking page...")
            # Take a screenshot for debugging
            page.screenshot(path=f"/tmp/reddit_dm_{username}.png")
            return "unknown"
    except Exception as e:
        print(f"  Error clicking send: {e}")
        return "send_error"

def try_new_reddit_message(page, username):
    """Try sending via new reddit message compose."""
    url = f"https://www.reddit.com/message/compose/?to={username}"
    print(f"  Trying new.reddit.com compose for u/{username}...")
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)

    page_text = page.content()

    # Try to find and fill subject field
    try:
        # New reddit has different selectors
        subject_input = page.locator('input[placeholder*="Subject"]').first
        if subject_input.count() == 0:
            subject_input = page.locator('input[name="subject"]').first
        if subject_input.count() > 0:
            subject_input.fill(SUBJECT)
            time.sleep(0.5)
        else:
            print(f"  No subject field on new reddit")
            return "no_form"
    except Exception as e:
        print(f"  Error: {e}")
        return "no_form"

    # Fill message
    try:
        msg_area = page.locator('textarea').first
        if msg_area.count() == 0:
            msg_area = page.locator('[contenteditable="true"]').first
        if msg_area.count() > 0:
            msg_area.fill(MESSAGE)
            time.sleep(0.5)
        else:
            return "no_form"
    except Exception as e:
        return "no_form"

    # Send
    try:
        send_btn = page.locator('button:has-text("Send")').first
        if send_btn.count() > 0:
            send_btn.click()
            time.sleep(3)
            return "sent"
    except:
        pass

    return "unknown"

def try_reddit_chat(page, username):
    """Try sending via Reddit chat as fallback."""
    print(f"  Trying Reddit chat for u/{username}...")
    page.goto("https://www.reddit.com/chat", wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)

    # Try to start a new chat
    try:
        # Look for new chat / compose button
        new_chat = page.locator('[aria-label*="new"]').first
        if new_chat.count() == 0:
            new_chat = page.locator('button:has-text("New Chat")').first
        if new_chat.count() == 0:
            new_chat = page.locator('[data-testid="create-chat"]').first

        if new_chat.count() > 0:
            new_chat.click()
            time.sleep(2)

            # Type username
            user_input = page.locator('input[placeholder*="user"]').first
            if user_input.count() == 0:
                user_input = page.locator('input[type="text"]').first
            if user_input.count() > 0:
                user_input.fill(username)
                time.sleep(1)
                # Select from dropdown
                page.locator(f'text=u/{username}').first.click()
                time.sleep(1)

                # Start chat
                start_btn = page.locator('button:has-text("Start")').first
                if start_btn.count() > 0:
                    start_btn.click()
                    time.sleep(2)

                # Type message
                msg_input = page.locator('[contenteditable="true"]').first
                if msg_input.count() == 0:
                    msg_input = page.locator('textarea').first
                if msg_input.count() > 0:
                    msg_input.fill(MESSAGE)
                    time.sleep(0.5)
                    page.keyboard.press("Enter")
                    time.sleep(2)
                    print(f"  Chat sent to u/{username}")
                    return "chat_sent"

        print(f"  Could not initiate chat with u/{username}")
        return "chat_failed"
    except Exception as e:
        print(f"  Chat error: {e}")
        return "chat_failed"


def scrape_targets_from_subs(page):
    """Scrape usernames from creator advice subreddits who are asking for promo help."""
    targets = []
    subs = [
        "OnlyFansAdvice",
        "CreatorsAdvice",
        "fansly_advice",
        "onlyfansadvice",
    ]

    search_terms = ["promotion", "promote", "traffic", "grow", "marketing", "subscribers", "fans", "views"]

    for sub in subs:
        print(f"\nScraping r/{sub} for creators needing promo help...")
        # Use old reddit JSON API
        for term in search_terms[:3]:  # Limit search terms
            url = f"https://old.reddit.com/r/{sub}/search.json?q={term}&restrict_sr=on&sort=new&t=month&limit=25"
            try:
                response = page.request.get(url, timeout=15000)
                if response.ok:
                    data = response.json()
                    children = data.get("data", {}).get("children", [])
                    for child in children:
                        author = child.get("data", {}).get("author", "")
                        title = child.get("data", {}).get("title", "")
                        if author and author not in SKIP and author != "[deleted]" and author != "AutoModerator":
                            if author not in [t[0] for t in targets]:
                                targets.append((author, title[:80], sub))
                                print(f"  Found: u/{author} — {title[:60]}")
                time.sleep(1)
            except Exception as e:
                print(f"  Error searching r/{sub}: {e}")
                continue

    return targets


def main():
    print("=" * 60)
    print("Reddit DM Outreach Script")
    print("=" * 60)

    cookies = load_cookies()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Set cookies
        context.add_cookies(cookies)
        page = context.new_page()

        # Verify login
        print("\nVerifying Reddit login...")
        page.goto("https://old.reddit.com", wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        content = page.content()

        if "Affectionate_Lunch_9" in content or "logout" in content.lower():
            print("Logged in as u/Affectionate_Lunch_9")
        else:
            print("WARNING: May not be logged in. Checking...")
            page.goto("https://old.reddit.com/user/me", wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
            if "Affectionate_Lunch_9" in page.content():
                print("Confirmed logged in.")
            else:
                print("NOT LOGGED IN. Attempting login with credentials...")
                page.goto("https://old.reddit.com/login", wait_until="domcontentloaded", timeout=15000)
                time.sleep(2)
                try:
                    page.fill('input[name="user"]', "Affectionate_Lunch_9")
                    page.fill('input[name="passwd"]', "3005059Krb$")
                    page.click('button[type="submit"]')
                    time.sleep(5)
                    if "Affectionate_Lunch_9" in page.content() or "logout" in page.content().lower():
                        print("Login successful!")
                    else:
                        print("Login may have failed. Continuing anyway...")
                except Exception as e:
                    print(f"Login error: {e}")

        # First, scrape targets from the advice subs
        print("\n" + "=" * 60)
        print("Phase 1: Scraping creator advice subs for targets")
        print("=" * 60)

        scraped = scrape_targets_from_subs(page)

        if not scraped:
            print("No targets found from scraping. Using manual approach...")
            # If scraping fails, we'll try direct JSON API
            try:
                import urllib.request
                import json as json2

                subs_to_check = ["OnlyFansAdvice", "CreatorsAdvice", "fansly_advice"]
                for sub in subs_to_check:
                    url = f"https://www.reddit.com/r/{sub}/new.json?limit=50"
                    headers = {"User-Agent": "Mozilla/5.0"}
                    req = urllib.request.Request(url, headers=headers)
                    resp = urllib.request.urlopen(req, timeout=10)
                    data = json2.loads(resp.read())
                    for child in data.get("data", {}).get("children", []):
                        author = child["data"].get("author", "")
                        title = child["data"].get("title", "")
                        flair = child["data"].get("link_flair_text", "")
                        # Look for posts about promotion/traffic/marketing
                        text_lower = (title + " " + str(flair)).lower()
                        promo_keywords = ["promot", "traffic", "grow", "market", "subscri", "fan", "view", "exposure", "boost", "engagement"]
                        if any(kw in text_lower for kw in promo_keywords):
                            if author and author not in SKIP and author != "[deleted]" and author != "AutoModerator":
                                if author not in [t[0] for t in scraped]:
                                    scraped.append((author, title[:80], sub))
                                    print(f"  Found: u/{author} — {title[:60]}")
                    time.sleep(1)
            except Exception as e:
                print(f"  Fallback scraping error: {e}")

        print(f"\nTotal targets found: {len(scraped)}")

        # Filter out skip list one more time
        targets = [(u, t, s) for u, t, s in scraped if u not in SKIP]
        print(f"After filtering skip list: {len(targets)}")

        if not targets:
            print("No valid targets found. Exiting.")
            browser.close()
            return

        # Phase 2: Send messages
        print("\n" + "=" * 60)
        print("Phase 2: Sending DMs")
        print("=" * 60)

        results = {"sent": [], "failed": [], "rate_limited": [], "blocked": [], "no_dms": [], "unknown": []}

        for i, (username, post_title, source_sub) in enumerate(targets):
            print(f"\n[{i+1}/{len(targets)}] Messaging u/{username} (from r/{source_sub})")
            print(f"  Post: {post_title}")

            result = try_old_reddit_message(page, username, results)

            if result == "sent":
                results["sent"].append(username)
            elif result == "rate_limited":
                results["rate_limited"].append(username)
                print("  Waiting 60s due to rate limit...")
                time.sleep(60)
                # Retry once
                result2 = try_old_reddit_message(page, username, results)
                if result2 == "sent":
                    results["sent"].append(username)
                else:
                    results["failed"].append((username, result2))
            elif result == "no_form" or result == "login_failed":
                # Try new reddit
                result2 = try_new_reddit_message(page, username)
                if result2 == "sent":
                    results["sent"].append(username)
                else:
                    # Try chat
                    result3 = try_reddit_chat(page, username)
                    if result3 == "chat_sent":
                        results["sent"].append(username)
                    else:
                        results["failed"].append((username, f"{result}->{result2}->{result3}"))
            elif result == "blocked":
                results["blocked"].append(username)
            elif result == "no_dms":
                results["no_dms"].append(username)
                # Try chat as fallback
                result2 = try_reddit_chat(page, username)
                if result2 == "chat_sent":
                    results["sent"].append(username)
            elif result == "user_not_found":
                results["failed"].append((username, "not_found"))
            else:
                results["unknown"].append(username)

            # Random delay between messages (15-45 seconds)
            if i < len(targets) - 1:
                delay = random.randint(15, 45)
                print(f"  Waiting {delay}s before next message...")
                time.sleep(delay)

        # Final report
        print("\n" + "=" * 60)
        print("OUTREACH RESULTS")
        print("=" * 60)
        print(f"Total targets: {len(targets)}")
        print(f"Successfully sent: {len(results['sent'])}")
        print(f"Rate limited: {len(results['rate_limited'])}")
        print(f"Blocked: {len(results['blocked'])}")
        print(f"No DMs accepted: {len(results['no_dms'])}")
        print(f"Failed: {len(results['failed'])}")
        print(f"Unknown: {len(results['unknown'])}")

        if results["sent"]:
            print(f"\nSent to: {', '.join(results['sent'])}")
        if results["failed"]:
            print(f"\nFailed: {', '.join([f'{u}({r})' for u,r in results['failed']])}")

        browser.close()

if __name__ == "__main__":
    main()
