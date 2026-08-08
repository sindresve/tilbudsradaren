from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from ..utils.deps import get_db
from ..utils.utils import current_year_week
from main import scan

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])

scheduler = BackgroundScheduler()
scheduler.start()

JOB_ID = "weekly_scan"


def has_scanned_this_week(conn) -> bool:
    year, week = current_year_week()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM catalogs WHERE year = ? AND week = ? LIMIT 1",
        (year, week),
    )
    return cursor.fetchone() is not None


def _next_monday_6am() -> datetime:
    now = datetime.now()
    days_ahead = (7 - now.weekday()) % 7  
    if days_ahead == 0:
        days_ahead = 7
    next_monday = (now + timedelta(days=days_ahead)).replace(
        hour=6, minute=0, second=0, microsecond=0
    )
    return next_monday


def _schedule_next_monday():
    scheduler.add_job(
        scan,
        trigger=CronTrigger(day_of_week="mon", hour=6, minute=0),
        id=JOB_ID,
        replace_existing=True,
    )


def run_scan_and_reschedule():
    scan()
    _schedule_next_monday()


def ensure_scheduled(conn):
    is_sunday = datetime.now().weekday() == 6  # Monday=0 ... Sunday=6

    if not is_sunday and not has_scanned_this_week(conn):
        scheduler.add_job(run_scan_and_reschedule, id="catchup_scan", replace_existing=True)
    else:
        _schedule_next_monday()


@router.post("/start")
def start_scheduler(background_tasks: BackgroundTasks, conn=Depends(get_db)):
    if not scheduler.get_job(JOB_ID):
        ensure_scheduled(conn)

    print("Scan scheduled")
    return _status(conn)


@router.post("/stop")
def stop_scheduler(conn=Depends(get_db)):
    if scheduler.get_job(JOB_ID):
        scheduler.remove_job(JOB_ID)
    if scheduler.get_job("catchup_scan"):
        scheduler.remove_job("catchup_scan")

    print("Scan stopped")
    return _status(conn)


@router.post("/run-now")
def run_now(background_tasks: BackgroundTasks):
    background_tasks.add_task(scan)

    print("Scan started")
    return {"status": "scan started"}


@router.get("/status")
def get_status(conn=Depends(get_db)):
    return _status(conn)


def _status(conn):
    job = scheduler.get_job(JOB_ID)
    return {
        "running": job is not None,
        "next_run": job.next_run_time.isoformat() if job else None,
        "scanned_this_week": has_scanned_this_week(conn),
    }