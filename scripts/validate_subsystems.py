import asyncio
import sys
import os

# Ensure backend is in path
sys.path.append(os.path.abspath("backend"))

from core.logger import get_logger
logger = get_logger("validate.subsystems")

async def validate_subsystem(name, startup_fn):
    logger.info(f"Validating Subsystem: {name}...")
    try:
        # Most subsystems are classes with start() or similar
        res = startup_fn()
        if asyncio.iscoroutine(res):
            await res
        logger.info(f"Subsystem {name}: BOOT ATTEMPTED")
        return True
    except Exception as e:
        logger.error(f"Subsystem {name}: BOOT FAILED - {e}")
        return False

async def main():
    print("--- F.R.I.D.A.Y. Subsystem Boot Validation ---")
    
    from core.event_bus import event_bus
    from core.task_manager import background_agent
    from desktop.file_manager import file_manager
    from desktop.tray_manager import tray_manager
    
    # Define testable startup flows
    subsystems = [
        ("EventBus", event_bus.start),
        ("BackgroundAgent", background_agent.start),
        ("FileManager", lambda: asyncio.to_thread(file_manager.start)),
        ("TrayManager", lambda: asyncio.to_thread(tray_manager.start)),
    ]
    
    results = []
    for name, fn in subsystems:
        res = await validate_subsystem(name, fn)
        results.append((name, res))
        await asyncio.sleep(0.5)

    print("\n--- Validation Summary ---")
    for name, res in results:
        status = "PASS" if res else "FAIL"
        print(f"{name}: {status}")

    # Generate Report
    os.makedirs("docs", exist_ok=True)
    with open("docs/SUBSYSTEM_HEALTH_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# Subsystem Health Report\n\n")
        f.write("| Subsystem | Status | Detail |\n| :--- | :--- | :--- |\n")
        for name, res in results:
            f.write(f"| {name} | {'PASS' if res else 'FAIL'} | {'Operational' if res else 'Check Logs'} |\n")

if __name__ == "__main__":
    asyncio.run(main())
