import asyncio
import sys
import os
import time
from playwright.async_api import async_playwright

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

async def run_golden_test(url="http://localhost:5174/assistant"):
    print("====================================================")
    print("      JARVIS GLOBAL PROFILE MEMORY VALIDATOR        ")
    print("====================================================")
    print(f"Target url: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Helper to click "Chats" and "New Chat"
        async def create_new_chat(page):
            chats_tab = page.locator("button:has-text('Chats')").first
            if await chats_tab.count() > 0:
                await chats_tab.click()
                await page.wait_for_timeout(500)
                
            new_chat_btn = page.locator("button:has-text('New Chat')").first
            if await new_chat_btn.count() > 0:
                await new_chat_btn.click()
                await page.wait_for_timeout(2000)
            return page.locator("input[type='text'], textarea").first

        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("Navigating to JARVIS assistant page...")
            await page.goto(url, timeout=20000, wait_until="domcontentloaded")
            await page.wait_for_timeout(4000)
            
            # Dismiss onboarding if visible
            onboarding_btn = page.locator("button:has-text('Initialize Workspace')")
            if await onboarding_btn.count() > 0 and await onboarding_btn.is_visible():
                print("Dismissing onboarding screen...")
                await onboarding_btn.click()
                await page.wait_for_timeout(1000)

            # ----------------------------------------------------
            # TEST A & B: Profile persistence and conversation isolation
            # ----------------------------------------------------
            print("\n--- TEST A & B: Scope Routing & Cross-Session Isolation ---")
            print("[Chat A] Creating Chat A...")
            chat_input_a = await create_new_chat(page)
            
            print("[Chat A] Storing profile fact: 'my favorite color is blue'")
            await chat_input_a.click()
            await chat_input_a.fill("my favorite color is blue")
            await page.wait_for_timeout(500)
            await chat_input_a.press("Enter")
            await page.wait_for_timeout(4000)

            print("[Chat A] Storing session fact: 'my current bug is websocket'")
            await chat_input_a.click()
            await chat_input_a.fill("my current bug is websocket")
            await page.wait_for_timeout(500)
            await chat_input_a.press("Enter")
            await page.wait_for_timeout(4000)

            # Start Chat B to verify recall isolation
            print("[Chat B] Creating Chat B...")
            chat_input_b = await create_new_chat(page)

            print("[Chat B] Querying profile fact: 'what is my favorite color'")
            await chat_input_b.click()
            await chat_input_b.fill("what is my favorite color")
            await page.wait_for_timeout(500)
            await chat_input_b.press("Enter")
            await page.wait_for_timeout(4000)

            friday_bubbles = page.locator(".justify-start")
            count = await friday_bubbles.count()
            last_text = await friday_bubbles.last.inner_text() if count > 0 else ""
            lines = [l.strip() for l in last_text.split("\n") if l.strip()]
            color_ans = lines[0] if lines else ""
            print(f"[Chat B] Color recall response: '{color_ans}'")

            print("[Chat B] Querying session fact: 'what is my current bug'")
            await chat_input_b.click()
            await chat_input_b.fill("what is my current bug")
            await page.wait_for_timeout(500)
            await chat_input_b.press("Enter")
            await page.wait_for_timeout(4000)

            friday_bubbles = page.locator(".justify-start")
            count = await friday_bubbles.count()
            last_text = await friday_bubbles.last.inner_text() if count > 0 else ""
            lines = [l.strip() for l in last_text.split("\n") if l.strip()]
            bug_ans = lines[0] if lines else ""
            print(f"[Chat B] Bug recall response: '{bug_ans}'")

            # ----------------------------------------------------
            # TEST C: Conflict Resolution (Latest User-Declared Write Wins)
            # ----------------------------------------------------
            print("\n--- TEST C: Conflict Resolution (Latest Write Wins) ---")
            print("Sending statement: 'my dog name is max'")
            await chat_input_b.click()
            await chat_input_b.fill("my dog name is max")
            await page.wait_for_timeout(500)
            await chat_input_b.press("Enter")
            await page.wait_for_timeout(4000)

            print("Sending statement: 'my dog name is rocky'")
            await chat_input_b.click()
            await chat_input_b.fill("my dog name is rocky")
            await page.wait_for_timeout(500)
            await chat_input_b.press("Enter")
            await page.wait_for_timeout(4000)

            print("Sending query: 'what is my dog name'")
            await chat_input_b.click()
            await chat_input_b.fill("what is my dog name")
            await page.wait_for_timeout(500)
            await chat_input_b.press("Enter")
            await page.wait_for_timeout(4000)

            friday_bubbles = page.locator(".justify-start")
            count = await friday_bubbles.count()
            last_text = await friday_bubbles.last.inner_text() if count > 0 else ""
            lines = [l.strip() for l in last_text.split("\n") if l.strip()]
            dog_ans = lines[0] if lines else ""
            print(f"Dog name recall response: '{dog_ans}'")

            # ----------------------------------------------------
            # TEST D: Persistence after refresh and cold reload
            # ----------------------------------------------------
            print("\n--- TEST D: Persistence & Refresh Verification ---")
            print("Refreshing browser/re-creating browser context...")
            await context.close()
            
            # Re-create fresh context & page to simulate a total browser reboot
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(url, timeout=20000, wait_until="domcontentloaded")
            await page.wait_for_timeout(4000)

            # Create fresh session Chat C
            print("[Chat C] Creating cold fresh Chat C...")
            chat_input_c = await create_new_chat(page)

            print("[Chat C] Querying persistent fact: 'what is my dog name'")
            await chat_input_c.click()
            await chat_input_c.fill("what is my dog name")
            await page.wait_for_timeout(500)
            await chat_input_c.press("Enter")
            await page.wait_for_timeout(4000)

            friday_bubbles = page.locator(".justify-start")
            count = await friday_bubbles.count()
            last_text = await friday_bubbles.last.inner_text() if count > 0 else ""
            lines = [l.strip() for l in last_text.split("\n") if l.strip()]
            cold_dog_ans = lines[0] if lines else ""
            print(f"[Chat C] Dog name recall response: '{cold_dog_ans}'")

            # Check all assertions
            success_a = (color_ans == "Blue.")
            success_b = (bug_ans == "I don't know.")
            success_c = (dog_ans == "Rocky.")
            success_d = (cold_dog_ans == "Rocky.")
            
            success = success_a and success_b and success_c and success_d
            
            print("\n====================================================")
            print("         GLOBAL PROFILE MEMORY BROWSER RESULTS      ")
            print("====================================================")
            print(f"Test A (Profile Cross-Session color): '{color_ans}' {'[OK]' if success_a else '[FAIL]'}")
            print(f"Test B (Conversation Isolated bug):    '{bug_ans}' {'[OK]' if success_b else '[FAIL]'}")
            print(f"Test C (Latest write wins dog name):    '{dog_ans}' {'[OK]' if success_c else '[FAIL]'}")
            print(f"Test D (Persistent Dog Name Recall):  '{cold_dog_ans}' {'[OK]' if success_d else '[FAIL]'}")
            print("====================================================")

            await browser.close()
            return success, f"A: {color_ans}, B: {bug_ans}, C: {dog_ans}, D: {cold_dog_ans}"
            
        except Exception as err:
            print(f"Error during browser golden test: {err}")
            await browser.close()
            return False, str(err)

if __name__ == "__main__":
    success, result = asyncio.run(run_golden_test())
    if not success:
        sys.exit(1)
