# Feature: Maintenance Due Alerts

## Summary
Give plant managers an at-a-glance view of which assets are overdue for scheduled
service, so they can act before equipment fails and stops the production line.

## The Problem
The asset tracker today is a passive inventory list. It tells you what equipment
exists and where it is, but not what needs attention. Managers have no simple way
to know which assets have missed their scheduled maintenance. Missed preventive
maintenance is a leading cause of unplanned equipment failure, and unplanned
downtime is expensive.

## The Solution
Every asset carries a "next service date." The dashboard reads that date and
automatically flags any asset whose service date has passed as **Overdue**. The
manager sees the overdue count the moment they open the dashboard and can filter
down to a ready-made work list in one click.

## Business Value
- Turns a passive inventory list into a proactive maintenance tool.
- Makes overdue service visible at a glance instead of buried in records.
- Reduces unplanned downtime by prompting action before a breakdown.
- Gives managers a prioritized work list without manual review.

## What Changes for the User

### 1. Overdue count front and center
A new summary card, **"Overdue for Service,"** joins the counts at the top of the
dashboard. It shows a live number of how many assets are past due, in Rockwell Red
so it stands out. Zero overdue reads as a healthy plant at a glance.

### 2. Clear flags in the asset list
The asset table gains a **"Next Service"** date column and an **"Overdue"** flag on
any asset that has missed its service date. Overdue rows are visually distinct, so
problem assets jump out from the rest of the list.

### 3. One-click work list
A **"Show overdue only"** filter lets the manager narrow the table to just the
assets that need service. Clicking the Overdue summary card does the same thing,
turning the count into an instant action list.

### 4. Service date when adding or editing an asset
When adding a new asset or opening an existing one, the manager can set or update
its **Next Service Date**, so the tracker stays current as maintenance gets
scheduled.

## Where It Shows Up
- **Top summary cards** — new "Overdue for Service" count.
- **Asset table** — new service date column and overdue flag.
- **Filter bar** — new "show overdue only" toggle.
- **Add asset form** — new service date field.
- **Asset detail panel** — view and update the service date, overdue flag if late.

## Scope for This Version
This first version surfaces overdue status based on a single service date per asset.
It is read-and-flag only. Full maintenance logging, service history, and automated
scheduling are intentionally out of scope and would be a later feature.

## What Success Looks Like
A manager opens the dashboard, immediately sees how many assets are overdue, clicks
to see exactly which ones, and knows what to service next, without reading through
the full inventory.
