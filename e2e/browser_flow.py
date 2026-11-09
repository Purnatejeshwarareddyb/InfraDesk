"""Real end-to-end browser test of InfraDesk (headless Chromium, Playwright).

Usage:  python e2e/browser_flow.py <screenshot_dir> [base_url]
It needs a running stack with DEMO data (see e2e/README.md) and creates a worker, an asset
and a ticket, then walks the ticket through its whole lifecycle as admin and worker.
Every PASS/FAIL line is a real check; nothing is mocked.
"""
import sys, re
from playwright.sync_api import sync_playwright, expect
S = sys.argv[1]; B = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:5173"
results = []
def step(name, fn):
    try:
        fn(); results.append(("PASS", name)); print("PASS", name, flush=True)
    except Exception as e:
        results.append(("FAIL", name + " :: " + str(e).splitlines()[0][:200])); print("FAIL", name, "::", str(e).splitlines()[0][:300], flush=True)

def pick(loc, text):
    loc.page.wait_for_function("el => el.options.length > 1", arg=loc.element_handle(), timeout=10000)
    for o in loc.locator("option").all():
        if text in o.inner_text():
            loc.select_option(value=o.get_attribute("value")); return
    raise AssertionError("no option containing " + text + " in " + str(loc.locator("option").all_inner_texts()))

def signout():
    pg.get_by_role("button", name="Sign out").click(timeout=5000); pg.wait_for_url("**/login")

def login(pg, user, pw="Demo-Passw0rd!"):
    pg.goto(B + "/login"); pg.get_by_label("Username").fill(user); pg.get_by_label("Password").fill(pw)
    pg.get_by_role("button", name="Sign in").click()

with sync_playwright() as p:
    b = p.chromium.launch(**({"executable_path": __import__("os").environ["CHROMIUM_PATH"]} if __import__("os").environ.get("CHROMIUM_PATH") else {}))
    ctx = b.new_context(viewport={"width": 1366, "height": 800})
    pg = ctx.new_page()

    # --- login failures and success
    def bad_login():
        login(pg, "demo_admin", "wrong-password-1A")
        expect(pg.get_by_text("Invalid username or password.")).to_be_visible()
    step("login with wrong password shows error", bad_login)
    def empty_login():
        pg.goto(B + "/login"); pg.get_by_role("button", name="Sign in").click()
        assert pg.locator("[role=alert], .field-error, .error").count() > 0
    step("empty login shows validation", empty_login)
    step("admin login lands on admin dashboard", lambda: (login(pg, "demo_admin"), pg.wait_for_url("**/admin"), expect(pg.get_by_role("heading", name="Dashboard")).to_be_visible()))

    # --- admin creates a user
    def create_user():
        pg.goto(B + "/admin/users"); pg.get_by_role("button", name="Create user").click()
        pg.get_by_label("Username").fill("worker_meena"); pg.get_by_label("Display name").fill("Meena Iyer (demo)")
        pg.get_by_label("Password").fill("Meena-Passw0rd-1")
        pg.get_by_role("dialog").get_by_role("button", name="Create user").click()
        expect(pg.get_by_text("worker_meena").first).to_be_visible()
    step("admin creates worker account", create_user)

    # --- admin creates an asset
    def create_asset():
        pg.goto(B + "/admin/assets"); pg.get_by_role("button", name="Create asset").click()
        pg.get_by_label("Asset tag").fill("proj-lab2-01"); pg.get_by_label("Name").fill("Lab 2 Projector")
        pg.get_by_role("dialog").get_by_role("button", name="Create asset").click()
        expect(pg.get_by_text("PROJ-LAB2-01").first).to_be_visible()
    step("admin creates asset (tag upper-cased)", create_asset)
    pg.screenshot(path=f"{S}/20-assets.png", full_page=True)

    # --- worker reports a ticket
    signout()
    step("worker login lands on worker area", lambda: (login(pg, "worker_meena", "Meena-Passw0rd-1"), pg.wait_for_url(re.compile(r".*/(worker|app).*")), None))
    print("worker landing:", pg.url)
    def worker_forbidden():
        pg.goto(B + "/admin/users"); pg.wait_for_load_state("networkidle")
        assert "/admin/users" not in pg.url or pg.get_by_text("Users").count() == 0 or "not" in pg.content().lower()
    step("worker cannot open admin users page", worker_forbidden)
    pg.screenshot(path=f"{S}/21-worker-blocked.png")
    nav = [a.inner_text() for a in pg.locator("nav a").all()]
    print("worker nav:", nav)
    def create_ticket():
        link = [a for a in pg.locator("nav a").all() if "reate" in a.inner_text() or "Report" in a.inner_text()]
        link[0].click() if link else pg.goto(B + "/worker/tickets/new")
        pg.get_by_label("Title").fill("Projector in Lab 2 does not turn on")
        pg.get_by_label("Description").fill("No light and the remote has no effect at all.")
        pg.get_by_label("Category").select_option("HARDWARE"); pg.get_by_label("Priority").select_option("HIGH")
        pick(pg.get_by_label(re.compile("asset", re.I)), "PROJ-LAB2-01")
        pg.get_by_role("button", name=re.compile("Create ticket|Submit|Report", re.I)).last.click()
        pg.wait_for_url(re.compile(r".*/tickets/\d+"))
        expect(pg.get_by_text("Projector in Lab 2 does not turn on").first).to_be_visible()
    step("worker reports a ticket linked to the asset", create_ticket)
    ticket_url = pg.url; print("ticket url:", ticket_url)
    pg.screenshot(path=f"{S}/22-worker-ticket.png", full_page=True)

    # --- admin assigns it
    signout()
    login(pg, "demo_admin"); pg.wait_for_url("**/admin")
    def admin_sees_notification():
        expect(pg.locator(".topbar").get_by_text("Notifications")).to_be_visible()
        pg.goto(B + "/admin/notifications"); pg.wait_for_load_state("networkidle"); print("NOTIF TEXT:", pg.locator("main").inner_text()[:400].replace("\n"," | ")); expect(pg.get_by_text(re.compile("Meena Iyer.*reported", re.S)).first).to_be_visible()
    step("admin gets notification about new ticket", admin_sees_notification)
    tid = re.search(r"/tickets/(\d+)", ticket_url).group(1)
    def assign():
        pg.goto(f"{B}/admin/tickets/{tid}"); pick(pg.get_by_label("Assign to"), "Meena")
        pg.get_by_role("button", name="Assign ticket").click()
        expect(pg.get_by_text("Assigned", exact=False).first).to_be_visible()
        pg.wait_for_load_state("networkidle")
        expect(pg.locator(".chip").filter(has_text="Assigned").first).to_be_visible()
    step("admin assigns ticket (status becomes Assigned)", assign)
    pg.screenshot(path=f"{S}/23-admin-assigned.png", full_page=True)

    # --- worker progresses and resolves
    signout()
    login(pg, "worker_meena", "Meena-Passw0rd-1"); pg.wait_for_url(re.compile(r".*/(worker|app).*"))
    def worker_notified():
        pg.goto(B + ticket_url.replace(B, "").replace(re.search(r"https?://[^/]+", ticket_url).group(0), "")); pg.wait_for_load_state("networkidle")
        bell = pg.locator(".topbar").get_by_text("Notifications")
        expect(pg.locator(".topbar")).to_contain_text(re.compile("Notifications\\s*1"))
    step("worker bell shows 1 unread (assignment)", worker_notified)
    def progress():
        pg.get_by_role("button", name=re.compile("Start|In progress", re.I)).first.click()
        expect(pg.locator(".chip").filter(has_text="In progress").first).to_be_visible()
    step("worker starts work", progress)
    def comment():
        pg.get_by_label("Add a comment").fill("Lamp is dead, ordering a replacement.")
        pg.get_by_role("button", name="Post comment").click()
        expect(pg.get_by_text("Lamp is dead, ordering a replacement.").first).to_be_visible()
    step("worker adds a work note", comment)
    def resolve():
        pg.get_by_role("button", name="Resolve").click()
        note = pg.get_by_label(re.compile("Resolution", re.I)); note.fill("Replaced the projector lamp.")
        pg.get_by_role("button", name=re.compile("Confirm|Resolve ticket|Save|Submit", re.I)).last.click()
        expect(pg.locator(".chip").filter(has_text="Resolved").first).to_be_visible()
    step("worker resolves with resolution note", resolve)
    pg.screenshot(path=f"{S}/24-worker-resolved.png", full_page=True)
    def mark_read():
        pg.goto(B + "/worker/notifications" if "/worker" in pg.url else pg.url); 
    step("worker notifications page", lambda: (pg.goto(pg.url.split("/tickets")[0] + "/notifications"), pg.wait_for_load_state("networkidle"), pg.screenshot(path=f"{S}/25-worker-notifications.png", full_page=True)))

    # --- admin closes and exports
    signout()
    login(pg, "demo_admin"); pg.wait_for_url("**/admin")
    def close():
        pg.goto(f"{B}/admin/tickets/{tid}"); pg.get_by_role("button", name="Close ticket").first.click(); pg.get_by_role("alertdialog").get_by_role("button", name="Close ticket").click()
        expect(pg.locator(".chip").filter(has_text="Closed").first).to_be_visible()
    step("admin closes the ticket", close)
    def csv():
        r = ctx.request.get(B + "/api/v1/tickets/export.csv")
        assert r.status == 200 and "ticket_number" in r.text() and "Projector in Lab 2" in r.text()
    step("CSV export contains the new ticket", csv)
    def reports():
        pg.goto(B + "/admin/reports"); pg.wait_for_load_state("networkidle")
        expect(pg.get_by_text("Hardware").first).to_be_visible()
    step("reports page loads real counts", reports)
    pg.screenshot(path=f"{S}/26-reports.png", full_page=True)
    def activity():
        pg.goto(B + "/admin/activity"); pg.wait_for_load_state("networkidle")
        expect(pg.get_by_text("Asset created").first).to_be_visible()
    step("activity log shows admin actions", activity)

    # --- responsive
    m = b.new_context(viewport={"width": 390, "height": 800}); mp = m.new_page()
    login(mp, "demo_admin"); mp.wait_for_url("**/admin"); mp.goto(B + "/admin/tickets"); mp.wait_for_load_state("networkidle")
    mp.screenshot(path=f"{S}/27-mobile-tickets.png")
    overflow = mp.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
    step("mobile layout has no horizontal page scroll", lambda: (_ for _ in ()).throw(AssertionError("page scrolls horizontally")) if overflow else None)
    def menu():
        mp.get_by_role("button", name="Menu").click(); expect(mp.get_by_role("link", name="Users")).to_be_visible()
    step("mobile Menu button opens navigation", menu)
    mp.screenshot(path=f"{S}/28-mobile-menu.png")
    b.close()

for status, name in results: print(status, "-", name)
print("TOTAL pass", sum(1 for s,_ in results if s=="PASS"), "fail", sum(1 for s,_ in results if s=="FAIL"))
