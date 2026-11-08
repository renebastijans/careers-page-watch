# Stopping and removing careers-page-watch

Nothing is installed on your computer system-wide, and nothing is stored online. Everything the tool made is in one folder, so removing it is simple.

## 1. Stop the daily run (if you set one up)
- **Claude route:** in the Claude app, click **Scheduled** in the left sidebar. Your tasks are listed under **Yours**. Click a careers-page-watch task to open it, select the **three dots** in the top-right corner, and choose **Delete**. Repeat for the backup task: there are usually two. Or open this folder in Claude and say: "list the scheduled tasks you created for careers-page-watch and delete them". It will ask you to confirm.
- **Terminal route with cron:** type `crontab -e`, delete the careers-page-watch line, save.
- If you never scheduled anything, there is nothing to stop.

### Leftovers from deleted tasks
Deleting a task in the app does not remove its folder. In testing, each deleted task left a folder behind in a hidden folder in your home directory, `~/.claude/scheduled-tasks`. The app no longer shows them and they do not run, but they stay on disk, and they make the app add a number to the names of new tasks (for example `job-ad-report-2`). To remove them, after you have deleted the tasks in the app:

1. In Finder choose **Go**, then **Go to Folder** (or press **Shift + Command + G**), and type `~/.claude/scheduled-tasks`. The folder is hidden, so you will not find it by browsing. If Finder still shows nothing, press **Shift + Command + .** (full stop) to show hidden files.
2. You will see one folder for every scheduled task you have ever made. The ones from this tool are named `job-ad-report` and `job-ad-report-backup` (sometimes with a number at the end), and in earlier versions `careers-page-watch-daily` and `careers-page-watch-backup`.
3. Select them (hold **Command** to pick several), right-click and choose **Move to Trash**. Move only those. Leave any folder you do not recognise: it may belong to another task of yours, and removing the folder of a task that is still active breaks that task.

## 2. Keep what you want
Your reports are in `data/reports/`. Copy any you want to keep somewhere else first.

## 3. Delete the folder
Drag the project folder (`careers-page-watch-main` if you downloaded the ZIP) to the Trash and empty it. This deletes your settings, the list of ads the tool has seen, and your reports.

## 4. Remove the setup chat (optional)
In the Claude app, delete the "Setup" conversation from the left sidebar.

## What stays, and why
- **Python.** Harmless; other programs may use it.
- **Your email connector in Claude** (for example Gmail), if you connected one for this. Remove it in Claude's settings if you no longer need it.
- **Emails already sent** stay in your inbox until you delete them.
- **Nothing on GitHub or elsewhere:** the tool never uploads anything.
