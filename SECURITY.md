# Security

This is a personal project, offered as is, best effort, with no support commitment.

- **Report a problem privately** with the "Report a vulnerability" button on this repo's **Security** tab. Please do not open a public issue for a security problem, and do not paste personal data. If the button is not there, open an issue titled "Security contact" with no details in it, and I will reply with a private way to reach me.
- **Ads and search results are untrusted text.** The scripts only parse them. In the optional Claude layer the instructions treat ad text as data, never as instructions: the agent reads, writes only inside your data folder, and emails only the address you set in `report_email_to`. It never applies for anything or contacts anyone else.
- **Scheduled runs use Auto mode.** A Claude scheduled task acts without asking first, so those limits are the safeguard. Review what a task is allowed to do under **Scheduled** in the Claude app, and check your reports now and then.
- **No secrets in the repo.** Your settings, seen ads and reports live in `data/` (gitignored) or the folder in `CPW_DATA`. Do not commit them, and do not paste them into an issue.
- **Network use.** The tool makes read-only requests to the public job-board endpoints of the employers you list, one scan a day, and never sends your data anywhere else.
