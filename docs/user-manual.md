# User manual

Open `http://localhost:8080` and sign in. Passwords are never shown or e-mailed; an administrator can reset yours, and you can change it yourself (worker: Account, administrator: Settings).

## Worker
- **Dashboard**: counts of your tickets.
- **Tickets**: only tickets you reported or that are assigned to you. Search, filter by status or priority, sort and page.
- **Report a fault** (Tickets, New): title, description, priority, and optionally the affected asset.
- **Ticket page**: description, history, comments. For an assigned ticket use the buttons shown (Start work, Resolve, and so on); only legal next steps appear. Resolving needs a resolution note.
- **Notifications**: the bell shows unread items; open the page to read them or mark all as read.

## Administrator
- **Dashboard and Reports**: counts by status, priority and asset, computed from real records, with a date range.
- **Tickets**: all tickets; assign to a worker, change status, close (confirmation asked), reopen, cancel; export the current filter to CSV.
- **Assets**: add, edit, search and retire equipment (asset tags are unique; retired assets cannot receive new tickets).
- **Users**: create users, set the role, deactivate, reset a password. The last active administrator cannot be removed or deactivated.
- **Activity**: audit log of administrative actions.

## Ticket status flow
Open, Assigned, In progress, Resolved, Closed, plus Cancelled and Reopened; exact table in `docs/workflow.md`.

## Phone
The layout adapts; use the Menu button to open the navigation.
