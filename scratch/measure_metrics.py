import asyncio
import sys
import os
import sqlite3
import time
import traceback
from playwright.async_api import async_playwright

async def measure_metrics(url="http://localhost:5173/assistant"):
    print("====================================================")
    print("           JARVIS HARDENING METRICS GATHERER        ")
    print("====================================================")
    
    metrics_report = {}
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=True,
            args=["--enable-precise-memory-info"] # Allow precise heap info in chrome
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        print(f"Navigating to browser target: {url}")
        try:
            # 1. Page Load
            response = await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            
            # Dismiss onboarding if visible
            onboarding_btn = page.locator("button:has-text('Initialize Workspace')")
            if await onboarding_btn.count() > 0 and await onboarding_btn.is_visible():
                print("Dismissing onboarding screen...")
                await onboarding_btn.click()
                await page.wait_for_timeout(1000)
            
            # Metric 1: DOM Node Count
            dom_nodes = await page.evaluate("() => document.getElementsByTagName('*').length")
            print(f"[*] DOM Nodes Count: {dom_nodes}")
            metrics_report["dom_nodes"] = dom_nodes
            
            # Metric 2: Peak Heap Memory
            heap_info = await page.evaluate("() => window.performance && window.performance.memory ? { used: window.performance.memory.usedJSHeapSize, total: window.performance.memory.totalJSHeapSize } : null")
            if heap_info:
                used_mb = round(heap_info["used"] / (1024 * 1024), 2)
                total_mb = round(heap_info["total"] / (1024 * 1024), 2)
                print(f"[*] Peak JS Heap Memory: {used_mb} MB (Total: {total_mb} MB)")
                metrics_report["peak_heap_mb"] = used_mb
            else:
                print("[*] Peak JS Heap Memory: N/A (performance.memory not supported)")
                metrics_report["peak_heap_mb"] = "N/A"
                
            # Metric 3: Render Latency (Send test message and measure time to update DOM)
            chat_input = page.locator("input[type='text'], textarea").first
            await chat_input.click()
            await chat_input.fill("System Health Check")
            
            # Send message and track render time
            start_time = time.time()
            await chat_input.press("Enter")
            
            # Wait for Friday to accept and render some text
            # We locate the last justify-start bubble (Friday's message)
            streaming_bubble = page.locator(".justify-start").last
            await streaming_bubble.wait_for(state="visible", timeout=5000)
            
            render_latency_ms = int((time.time() - start_time) * 1000)
            print(f"[*] Render Latency (first response paint): {render_latency_ms} ms")
            metrics_report["render_latency_ms"] = render_latency_ms
            
            # Metric 4: Duplicate DB Rows Check
            db_path = "backend/friday_memory.db"
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    # Check duplicate nonces
                    cursor.execute("SELECT request_nonce, COUNT(*) FROM messages WHERE request_nonce IS NOT NULL GROUP BY request_nonce HAVING COUNT(*) > 1")
                    duplicates_nonce = cursor.fetchall()
                    
                    # Check duplicate client_request_ids
                    cursor.execute("SELECT client_request_id, COUNT(*) FROM messages WHERE client_request_id IS NOT NULL GROUP BY client_request_id HAVING COUNT(*) > 1")
                    duplicates_client_id = cursor.fetchall()
                    
                    conn.close()
                    
                    dup_count = len(duplicates_nonce) + len(duplicates_client_id)
                    print(f"[*] Duplicate DB Rows check: {dup_count} duplicate rows found.")
                    metrics_report["duplicate_db_rows"] = dup_count
                except Exception as dbe:
                    print(f"[*] DB audit error: {dbe}")
                    metrics_report["duplicate_db_rows"] = f"DB check failed: {dbe}"
            else:
                print("[*] DB audit error: friday_memory.db not found.")
                metrics_report["duplicate_db_rows"] = "DB not found"

            # Metric 5: Scroll FPS
            # Scroll up and down inside the chat container to track frame rates
            scroll_container = page.locator("main, [class*='chat']").first
            
            # Measure frames over 1 second of scrolling
            fps_script = """
            async () => {
                let frameCount = 0;
                let startTime = performance.now();
                let isRunning = true;
                
                function countFrames() {
                    if (!isRunning) return;
                    frameCount++;
                    requestAnimationFrame(countFrames);
                }
                
                requestAnimationFrame(countFrames);
                
                // Perform scrolls
                const el = document.querySelector('main') || document.body;
                for (let i = 0; i < 20; i++) {
                    el.scrollTop = i * 20;
                    await new Promise(r => setTimeout(r, 20));
                }
                
                isRunning = false;
                let endTime = performance.now();
                let durationSeconds = (endTime - startTime) / 1000;
                return Math.round(frameCount / durationSeconds);
            }
            """
            scroll_fps = await page.evaluate(fps_script)
            print(f"[*] Scroll Performance: {scroll_fps} FPS")
            metrics_report["scroll_fps"] = scroll_fps
            
            # Metric 6: Restore Correctness (Scroll position switch & restore persistence)
            # Switch to Chats Tab
            print("Switching to Chats tab...")
            chats_tab_btn = page.locator("button:has-text('Chats')").first
            await chats_tab_btn.click()
            await page.wait_for_timeout(1000)
            
            # Click "New Chat" button to ensure at least two sessions exist
            print("Creating a new chat session to test persistence...")
            new_chat_btn = page.locator("button:has-text('New Chat')").first
            await new_chat_btn.click()
            await page.wait_for_timeout(1500)
            
            # 1. Type several messages in the current session to allow scrolling
            print("Populating messages in the new session to make it scrollable...")
            for msg_text in ["msg A", "msg B", "msg C", "msg D", "msg E"]:
                await chat_input.click()
                await chat_input.fill(msg_text)
                await chat_input.press("Enter")
                await page.wait_for_timeout(1000)
            
            # 2. Scroll up to some specific position (e.g., 200px)
            scroll_target = 200
            await page.evaluate(f"() => {{ const el = document.querySelector('main'); if (el) el.scrollTop = {scroll_target}; }}")
            await page.wait_for_timeout(500)
            
            actual_scroll = await page.evaluate("() => { const el = document.querySelector('main'); return el ? el.scrollTop : 0; }")
            print(f"[*] Set scroll container scrollTop to: {actual_scroll} px")
            
            # 3. Locate all session buttons in the Sidebar under Chats tab
            session_btns = await page.locator("div:has-text('CHAT HISTORY') + div > div").all()
            if len(session_btns) > 1:
                print(f"Switching session in Sidebar (total sessions: {len(session_btns)})...")
                # Click the second session button (index 1)
                await session_btns[1].click()
                await page.wait_for_timeout(1500)
                
                # Switch back to first session (index 0)
                print("Switching back to first session...")
                session_btns_reloaded = await page.locator("div:has-text('CHAT HISTORY') + div > div").all()
                await session_btns_reloaded[0].click()
                await page.wait_for_timeout(1500)
                
                # 4. Verify scroll position restored correctness
                restored_scroll = await page.evaluate("() => { const el = document.querySelector('main'); return el ? el.scrollTop : 0; }")
                scroll_diff = abs(restored_scroll - actual_scroll)
                
                restore_correct = scroll_diff < 15 # Tolerable difference of 15px due to virtualizer adjustments
                print(f"[*] Restored scroll position: {restored_scroll} px (Diff: {scroll_diff} px, Correct: {restore_correct})")
                metrics_report["restore_correctness"] = "PASSED" if restore_correct else f"FAILED (offset difference {scroll_diff}px)"
            else:
                print("[*] Skipping restore correctness check: not enough sessions to switch.")
                metrics_report["restore_correctness"] = "SKIPPED (Only one session available)"
            
        except Exception as err:
            print(f"[!] Gathering metrics failed: {err}")
            print(traceback.format_exc())
            metrics_report["error"] = str(err)
            
        await browser.close()
        
    print("\n====================================================")
    print("                 FINAL METRICS SUMMARY              ")
    print("====================================================")
    for k, v in metrics_report.items():
        print(f"  {k.replace('_', ' ').title()}: {v}")
    print("====================================================")
    return metrics_report

if __name__ == "__main__":
    asyncio.run(measure_metrics())
