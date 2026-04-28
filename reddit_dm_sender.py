#!/usr/bin/env python3
"""
Reddit DM sender using Playwright headless browser.
Fills the compose form and clicks Send for each target user.
Uses Playwright's fill() to properly trigger React state updates.
"""

import sys
import time
import json
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(line_buffering=True)

COOKIE_VALUE = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpsVFdYNlFVUEloWktaRG1rR0pVd1gvdWNFK01BSjBYRE12RU1kNzVxTXQ4IiwidHlwIjoiSldUIn0.eyJzdWIiOiJ0Ml83aWt0MWtoYyIsImV4cCI6MTc5MDIxNjI4MS43MjI2MDksImlhdCI6MTc3NDU3Nzg4MS43MjI2MDksImp0aSI6IjdCR2duZTEtaXF4eC1VcDN1eE4zZ1daOWNDUS1FUSIsImF0IjoxLCJjaWQiOiJjb29raWUiLCJsY2EiOjE1OTYzMjIzNzAxOTgsInNjcCI6ImVKeUtqZ1VFQUFEX193RVZBTGsiLCJmbG8iOjIsImFtciI6WyJwd2QiXX0.g_pObzjXfI2fUU4oc7e2nnKx1gQPMG1qsMSRww8-huBwQdL1lc2ny-kB8kkElbVxHgrVub4CGMWybz_M5VvNg16H-Hy16y1O6sDWb8SMFSX4huuQkPG6RNbr6C_xzVPKbKT7wjcBzFUbnr6kNZspeLRQA9sLyKELIN0J26pXKN9Nz3rfJOfi_t7ts3I_Ah0Dkz41bcbJS7CWxwI9QELHqpLkmFDRvfqJ_8-iGXCQev4NmxbUyMuOlaxuZybPxb9A2Da-B7DJ9FhazIfl6H2KpXnKFKEK3CocDQBIMi2l0uTEh_ctiKYkjwqli1TCJqQBWzl2t-vbMfUcrfu2hn0HUQ"

COOKIES = [
    {"name": "reddit_session", "value": COOKIE_VALUE, "domain": ".reddit.com", "path": "/"},
    {"name": "edgebucket", "value": "A3tqhYWiSSddCexajC", "domain": ".reddit.com", "path": "/"},
    {"name": "csv", "value": "2", "domain": ".reddit.com", "path": "/"},
]

# Classic_Bookkeeper88 already sent in test run - skip it
TARGETS = [
    "lovleylondon92", "ScarlettVale3", "Good-Huckleberry3395",
    "victoriaenglishrose", "cozycassie", "AdExact3789", "Introspective_Kiwi",
    "mewstic_", "Ok-Ocelot-774", "whimsyskill", "ilovemyfluffysockss",
    "sweett_sofia", "VoluptuousVen0m", "Soupypiemade", "tipsy_101",
    "CumBag24", "OutsidePlatform9864", "Femme-Fatale666", "Booziebunzz",
    "IamEmma_2025", "screamqueenP", "BusyBeingLiv", "Goodolethrowawayacct",
    "bbw_feede", "No_Amphibian_2159", "MinxieBinxie", "vulcanvampiire",
    "brittlesdeebby", "Sophiabby13", "Dulce_1234", "Murky-Breadfruit-291",
    "Georgiafun11", "SafeUnit5128", "Dry_Season_1103", "Typical_Anxiety_8131",
    "Pettitsugar", "Jadalavaux", "venusprive", "revnxage",
    "Weird-Opportunity420", "DommeKitty1", "Lucky-Squirrel-9857", "LatinaSnow",
    "Hottestgirl210", "Anxious-Work-6362", "Frequent-Complex3685", "viirtualgoth",
    "Aijimik", "Lanasecretshh", "stardewsglowing", "itsnotmykitten", "Elda_22"
]

SUBJECT = "Promo opportunity - 40K subscriber subreddit"

MESSAGE = "Hey! I run r/chibigbootygirls on Reddit - 40,000 subscribers, all into thick and curvy content.\n\nI saw your post about needing help with promotion and I think I can help. I promote creators through my sub - regular features, engagement, consistent traffic to your page. No cost, we just split what my traffic brings in.\n\n40K is a lot of eyeballs looking for exactly your type of content. Want to try a feature this week and see what happens?"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def send_dm(page, target, subject, message):
    """Send a DM by loading compose page, filling form, clicking Send."""
    url = "https://www.reddit.com/message/compose/?to=" + target

    try:
        page.goto(url, wait_until="load", timeout=60000)
        time.sleep(4)

        # Check for login redirect
        if "login" in page.url.lower():
            return False, "session_expired"

        # Check if compose form loaded
        try:
            page.locator('input[name="message-title"]').wait_for(state="visible", timeout=10000)
        except:
            # Maybe user doesn't exist or can't receive messages
            body = ""
            try:
                body = page.inner_text("body")[:300]
            except:
                pass
            if "doesn't exist" in body.lower() or "not found" in body.lower():
                return False, "user_not_found"
            return False, "form_not_loaded"

        # Fill title
        title_input = page.locator('input[name="message-title"]')
        title_input.click()
        time.sleep(0.3)
        title_input.fill(subject)
        time.sleep(0.3)

        # Fill message
        msg_textarea = page.locator('textarea[name="message-content"]')
        msg_textarea.click()
        time.sleep(0.3)
        msg_textarea.fill(message)
        time.sleep(0.3)

        # Verify fields are filled
        title_val = title_input.input_value()
        msg_val = msg_textarea.input_value()
        if not title_val or not msg_val:
            return False, "form_fill_failed"

        # Click Send
        send_btn = page.locator('button[type="submit"]:has-text("Send")')
        send_btn.click()

        # Wait for the form to clear (indicates success)
        time.sleep(4)

        # Check if form cleared (success indicator)
        try:
            new_title = title_input.input_value()
            if not new_title:
                # Form cleared = message sent
                return True, "sent"
            else:
                # Form still has content - check for error message
                body = ""
                try:
                    body = page.inner_text("body")[:500]
                except:
                    pass
                if "rate limit" in body.lower() or "too many" in body.lower():
                    return False, "rate_limited"
                if "blocked" in body.lower():
                    return False, "blocked"
                if "doesn't accept" in body.lower():
                    return False, "pm_restricted"
                # Form didn't clear but no obvious error
                return False, "send_failed_unknown"
        except:
            # If we can't read the input, page might have changed
            return True, "sent_likely"

    except Exception as e:
        return False, str(e)[:200]


def main():
    print("Starting Reddit DM sender...")
    print("Targets: " + str(len(TARGETS)) + " users")
    print("(Classic_Bookkeeper88 already sent in test run)")
    print("=" * 50)

    successes = ["Classic_Bookkeeper88"]  # Already sent
    failures = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=UA)
        context.add_cookies(COOKIES)
        page = context.new_page()

        for i, target in enumerate(TARGETS):
            print("\n[" + str(i+2) + "/53] u/" + target + "...")

            ok, result = send_dm(page, target, SUBJECT, MESSAGE)

            if ok:
                print("  SENT: " + result)
                successes.append(target)
            else:
                print("  FAILED: " + result)
                failures.append((target, result))

                if "session_expired" in result:
                    print("  SESSION EXPIRED - stopping")
                    break

                if "rate_limited" in result:
                    print("  Rate limited! Waiting 90s...")
                    time.sleep(90)

            # 30-second delay
            if i < len(TARGETS) - 1:
                print("  Waiting 30s...")
                time.sleep(30)

        browser.close()

    # Final report
    print("\n" + "=" * 50)
    print("FINAL REPORT")
    print("=" * 50)
    print("Total: 53 targets")
    print("Sent: " + str(len(successes)))
    print("Failed: " + str(len(failures)))

    if successes:
        print("\nSuccessful (" + str(len(successes)) + "):")
        for u in successes:
            print("  + u/" + u)

    if failures:
        print("\nFailed (" + str(len(failures)) + "):")
        for u, reason in failures:
            print("  - u/" + u + ": " + reason)


if __name__ == "__main__":
    main()
