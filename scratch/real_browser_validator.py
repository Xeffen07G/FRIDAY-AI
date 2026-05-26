import asyncio
import sys
import os
import re
import traceback
from playwright.async_api import async_playwright

async def run_browser_validation(url="http://localhost:5173/assistant", ws_url="ws://127.0.0.1:8000/api/ws/voice"):
    print("\n--- STAGE: PAGE_RENDER_CHECK & CONSOLE_ERROR_AUDIT ---")
    
    console_errors = []
    uncaught_exceptions = []
    failed_requests = []
    
    # Analyze errors for failure reporting
    def on_console(msg):
        if msg.type == "error":
            console_errors.append({
                "text": msg.text,
                "location": msg.location
            })
            print(f"[Browser Console Error] {msg.text} (at {msg.location})")

    def on_page_error(err):
        uncaught_exceptions.append({
            "message": err.message,
            "stack": err.stack or ""
        })
        print(f"[Browser Uncaught PageError] {err.message}\n{err.stack or ''}")

    def on_req_failed(req):
        err_msg = req.failure if req.failure else "Unknown request failure"
        failed_requests.append({
            "url": req.url,
            "error": err_msg
        })
        print(f"[Browser Request Failed] {req.url} -> {err_msg}")

    async with async_playwright() as p:
        # Launch browser headlessly (or with head if needed, but headless is standard for CI/automated testing)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Attach listeners
        page.on("console", on_console)
        page.on("pageerror", on_page_error)
        page.on("requestfailed", on_req_failed)
        
        print(f"Navigating to browser target: {url}")
        try:
            # 1. PAGE_RENDER_CHECK: Initial Page Load
            response = await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            status_code = response.status if response else None
            print(f"Page response status code: {status_code}")
            
            if not response or status_code != 200:
                raise Exception(f"Failed to load page. HTTP status: {status_code}")
                
            # Allow 3 seconds for initial compilation/load
            await page.wait_for_timeout(3000)
            
            # 2. Check for Vite compile error overlays
            vite_overlay = page.locator("vite-error-overlay")
            vite_overlay_count = await vite_overlay.count()
            if vite_overlay_count > 0:
                overlay_text = await vite_overlay.first.inner_text()
                raise Exception(f"Vite compilation / runtime error overlay detected:\n{overlay_text}")

            # 3. Check for React Error Boundary Activation
            body_text = await page.locator("body").inner_text()
            if "Something went wrong" in body_text:
                raise Exception("React ErrorBoundary is ACTIVE. Display layer has crashed.")

            # 4. Check for Root React Mount
            root_element = page.locator("#root")
            if await root_element.count() == 0:
                raise Exception("React Root mount element '#root' was NOT found in the page!")

            # 5. Handle Onboarding Overlay (dismiss it to make layout usable)
            onboarding_btn = page.locator("button:has-text('Initialize Workspace')")
            if await onboarding_btn.count() > 0 and await onboarding_btn.is_visible():
                print("Onboarding screen detected. Dismissing it by clicking 'Initialize Workspace'...")
                await onboarding_btn.click()
                await page.wait_for_timeout(1000)

            # Re-check Vite overlays & error boundaries after onboarding dismissal
            if await vite_overlay.count() > 0:
                overlay_text = await vite_overlay.first.inner_text()
                raise Exception(f"Vite error overlay detected after onboarding:\n{overlay_text}")
                
            if "Something went wrong" in await page.locator("body").inner_text():
                raise Exception("React ErrorBoundary is ACTIVE after onboarding.")

            # 6. Check AssistantPage Layout Components
            # The page should have a sidebar and a main workspace area
            sidebar_count = await page.locator(".sidebar, [class*='sidebar'], nav").count()
            chat_container_count = await page.locator("main, [class*='chat']").count()
            input_count = await page.locator("input[type='text'], textarea").count()

            print(f"Layout Audit: Sidebar={sidebar_count}, ChatContainer={chat_container_count}, Inputs={input_count}")
            if sidebar_count == 0:
                raise Exception("Layout unstable: Sidebar element was not found!")
            if chat_container_count == 0:
                raise Exception("Layout unstable: Message stream/Chat container was not found!")
            if input_count == 0:
                raise Exception("Layout unstable: Chat/Command input textarea or input was not found!")

            # 7. WEBSOCKET_CHECK: Check WebSocket connection indicator on frontend page
            # Look for websocket status badge
            ws_badge = page.locator(".w-1\\.5.h-1\\.5.rounded-full")
            ws_badge_count = await ws_badge.count()
            ws_connected = False
            
            # Search for status text 'online' or status badge color
            status_text = await page.locator("span:has-text('online'), span:has-text('offline')").first.inner_text() if await page.locator("span:has-text('online'), span:has-text('offline')").count() > 0 else "unknown"
            print(f"WebSocket Status Badge reads: {status_text}")
            
            if "online" in status_text.lower() or "connected" in status_text.lower():
                ws_connected = True
                print("WebSocket badge reports: ONLINE")
            else:
                # We can also check if the background-color is emerald or amber/red
                # Let's inspect class or styling of the status indicator dot
                print(f"Warning: WebSocket badge reports: {status_text}. Checking if it synchronizes...")
                # Wait up to 5 seconds to see if it connects
                for _ in range(5):
                    await page.wait_for_timeout(1000)
                    status_text = await page.locator("span:has-text('online'), span:has-text('offline')").first.inner_text() if await page.locator("span:has-text('online'), span:has-text('offline')").count() > 0 else "unknown"
                    if "online" in status_text.lower() or "connected" in status_text.lower():
                        ws_connected = True
                        print("WebSocket badge successfully synchronized to: ONLINE")
                        break
                if not ws_connected:
                    raise Exception(f"WebSocket badge remains disconnected: {status_text}")

            # 8. UI_INTERACTION_CHECK: Safely interact with the UI elements
            print("\n--- STAGE: UI_INTERACTION_CHECK ---")
            
            # Verify Sidebar mounts and behaves correctly
            # Click tabs in Sidebar if they exist. Sidebar.jsx shows tabs like 'Workspace', 'Memories', 'Engineering'
            tab_btn = page.locator("button:has-text('Workspace'), button:has-text('History'), button:has-text('Sync')").first
            if await tab_btn.count() > 0 and await tab_btn.is_visible():
                print(f"Clicking sidebar tab button to check stability...")
                await tab_btn.click()
                await page.wait_for_timeout(500)

            # Click UI command input, fill it with a command and submit it
            # The textarea usually handles typing and hitting Enter
            chat_input = page.locator("input[type='text'], textarea").first
            print("Locating command input and typing test command...")
            await chat_input.click()
            await chat_input.fill("ping")
            await page.wait_for_timeout(500)
            
            # Send message by pressing Enter or clicking send button
            print("Submitting the test command...")
            await chat_input.press("Enter")
            
            # Wait to ensure message stream renders and there is no sudden crash
            await page.wait_for_timeout(2000)
            
            # Verify message stream renders the message we typed
            body_text_after_submit = await page.locator("body").inner_text()
            if "ping" not in body_text_after_submit.lower():
                print("Warning: Message stream does not immediately show 'ping', checking for input clearing...")
                input_val = await chat_input.input_value()
                if input_val == "":
                    print("Input was successfully cleared, confirming submission was processed.")
                else:
                    raise Exception("UI Interaction Failed: Text was not cleared/submitted from input box!")

            # Final check of error boundaries and overlays after interaction
            if await vite_overlay.count() > 0:
                overlay_text = await vite_overlay.first.inner_text()
                raise Exception(f"React crashed after UI interaction! Vite overlay active:\n{overlay_text}")
                
            if "Something went wrong" in await page.locator("body").inner_text():
                raise Exception("React ErrorBoundary crashed after UI interaction!")

            # Audit console errors and page exceptions accumulated during session
            if len(uncaught_exceptions) > 0:
                raise Exception(f"Uncaught page exception(s) detected during session: {uncaught_exceptions[0]['message']}")
                
            # Filter console errors to avoid ignoring real problems, but exclude harmless network prefetch blocks
            real_errors = [e for e in console_errors if not any(x in e['text'].lower() for x in ["favicon", "chrome-extension"])]
            if len(real_errors) > 0:
                raise Exception(f"Uncaught console.error(s) detected: {real_errors[0]['text']}")

            print("\n=== ALL REAL UI VALIDATION CHECKS PASSED SUCCESSFULLY! ===")
            await browser.close()
            return {
                "success": True,
                "details": "Browser page renders successfully, no React runtime exceptions, no ErrorBoundary activation, no console errors, websocket connected, root React mount successful, layout stable and command input verified."
            }

        except Exception as e:
            # Failure Reporting Analysis
            print(f"\n!!! UI VALIDATION CRITICAL FAILURE !!!\nError: {e}")
            
            # Attempt to gather exact stack trace, file and component
            failing_file = "Unknown"
            stack_trace = "Not available"
            failing_component = "Unknown"
            probable_cause = str(e)
            
            # Parse from Playwright's uncaught page exceptions if available
            if len(uncaught_exceptions) > 0:
                first_exc = uncaught_exceptions[0]
                stack_trace = first_exc["stack"] or first_exc["message"]
                # Try to extract file and line from stack
                match = re.search(r"at\s+([^\s]+)\s+\((.+?):(\d+):(\d+)\)", stack_trace)
                if not match:
                    match = re.search(r"(.+?):(\d+):(\d+)", stack_trace)
                if match:
                    failing_file = match.group(2) if match.lastindex >= 2 else match.group(1)
                    probable_cause = f"Uncaught runtime exception: {first_exc['message']}"
            
            # Parse from Vite overlay if it was present
            vite_overlay_count = await page.locator("vite-error-overlay").count()
            if vite_overlay_count > 0:
                overlay_text = await page.locator("vite-error-overlay").first.inner_text()
                stack_trace = overlay_text
                # Look for file paths inside Vite overlay text
                lines = overlay_text.split("\n")
                for line in lines:
                    if "/" in line or "\\" in line or ".jsx" in line or ".js" in line:
                        failing_file = line.strip()
                        break
                probable_cause = "Vite compilation or module resolution failure."
            
            # Try to guess component from file path
            if "/" in failing_file or "\\" in failing_file:
                basename = os.path.basename(failing_file).split("?")[0]
                if basename.endswith(".jsx") or basename.endswith(".js"):
                    failing_component = basename.split(".")[0]
            
            await browser.close()
            return {
                "success": False,
                "error": str(e),
                "failing_file": failing_file,
                "stack_trace": stack_trace,
                "failing_component": failing_component,
                "probable_cause": probable_cause
            }

if __name__ == "__main__":
    asyncio.run(run_browser_validation())
