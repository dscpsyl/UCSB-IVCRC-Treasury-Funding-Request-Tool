# Changelog
#### Linked versions are to releases.
>`Added` for new features.
>`Changed` for changes in existing functionality.
>`Deprecated` for soon-to-be removed features.
>`Removed` for now removed features.
>`Fixed` for any bug fixes.
>`Security` in case of vulnerabilities.

## v1.0.3

### Changed
- Refactored bot code so that it is now in it's own folder with a main run file.
## v1.0.2

### Added
- Added weekly meeting reminders to the bot

### Fixed
- `main.py` now has the right `settings.json` file

## v1.0.1

### Added
- Requisition filler now helps you complete the type
- Persistent bot for workflows and webhooks
- `bot_run.py` for running the bot

### Fixed
- `requirements.txt` file now is fully up to date
- `newEntry` bugs
- `requesitionPre` bugs
- Email sending with attachment bugs

### Changed
- `run.py` from before is now `CLI_run.py`
- README.md file
- moved `settings.json` to root folder

## v1.0.0

### Added
- Initial Release

### Fixed
- `README.md` file

## v0.9.1-beta

### Added
- Auto highlighting of the meeting minutes
- Headder for requesition filler method
- `drive.driveMV()` method to move files in drive
- Move completed files to archive folder
- AutoTagging of signatures request based on a list of Slack IDs
- Sheet data get and update methods and auto linking funding agreement to spreadsheet

### Changed
- Added option for interview insted of report for follow up in agreement
- Reorganized menu for better flow
- DB display to remove pandas index for less confusion

### Removed
- Date Passed question. It is not automatically calculated based on meeting minute selected

### Fixed
- Payment checkin data issue

## v0.8.3-beta

### Added
- `shareFile` method to auto share the files with the approprate people
- Added logo to CLI for better looks
- Board comments to CLI
- Auto linking of follow up report to funding agreement

### Changed
- We now assume the user will input the year for us
- All print statements are now as logging for better practices
- All input lines start with the same symbol for easier reading
- `FAgreement.docx` now has better formatting and is more readable to humans
- No input when choosing minute ID now defults to the first one

## v0.8.2-beta

### Added
- `viewAllDB` method to print out all entries in the database with revelant info using pandas module
- `viewSingleDB` method to print out all data for a specific funding request number
- `deleteRequest` method to delete a specific funding request number from the database
- `updateData` method to update the data section of a funding request by number

### Fixed
- `requesitionPre` method for pdf merging
- `followupReport` database getting conneciton missing

### Changed
- Spelling mistake in `res/thankYou.html`

## v0.8.1-beta

### Changed
- Contracts with logos for the new and updated year
- `pdfFormFiller` method
- `requisitionForm` method to fill out requesition directly from commandline and database

### Fixed
- DatadbGet method with conn in main
- Requesition form in `res` now has proper form field names

## v0.8.0-beta

### Added
- File suggestions throughout google service
- Suggestions for requesition number
- Showing recent requesitions when adding information
- New methods for data collection
### Fixed
- Auto year update

## v0.7.0-beta

### Added 
- `driveLIST` method
- Minutes will now be suggested to the user when creating a new entry
- `checkin.html` will now be autodeleted after running
- Follow Up Report emails have been added

### Changed
- Database dataget is now its own function as `dataDBGet()`

### Fixed
- Spreadsheet insertion now updates existing rows so that the bar and previous calculations are not removed by new row insertion
- `[frenddate]` insertion in funding agreement is now fixed

## v0.5.0-beta

### Added
- Payment CheckIn on Sent Requisitions

## v0.4.2-beta

### Added
- Now uploading completed document to drive for archiving when requesition is sent

### Fixed
- File names for uploading to drive
- Typos
- File upload with pdf attachment
## v0.4.1-beta

### Added
- Gave user information to help fill out requesition

### Fixed
- Pdf Merging 
- Slack File Upload return value
- Typos

## v0.4.0-beta

### Added
- Pre-signature requesition steps
- New Sqlite functions
- New Slack File Functions 
- PDF Functions

### Changed
- Structure of database with new column
- 


## v0.3.0-beta

### Added
- Requesition Sending
- Requestee notification
- Sqlite Database Functions
### Changed
- Authentication Process
### Fixed
- Mispellings
- File overwrite errors
## v0.1.1-beta
### Fixed
- Misspellings 
- Bugs throughout `New Entry` method

## v0.1.0-beta

### Added
- Sqlite database & functions 
- Slack API and integration completed with dedicated App in workspace
- New Entry Function is basic and usable wih cmd line UI
### Changed
- Multiple `util` functions on the backend 


## v0.0.9-alpha

### Added
- Parts of multiple options have been added
- `Denied` function has been completed
- Most Google API helper functions have been created
  