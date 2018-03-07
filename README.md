# BallotSystem
A potential upgrade to the Trinity Hall balloting system
It was written in 2015/6 and updated 2018 to use the Google Drive API.
Further rewrite are needed/possible:
* rewrite frontend in React (would work very well with this app)

## Installation
* This should be set up for thjcr already, but in essence:
  * set up virtualenv (srcf doesn't allow installing packages)
  * `pip install gspread oauth2client`
  * Note: currently on python2 for pip usage
  * clone this repository
  * Add the google API key (should already be there if already set up)
  * Check permissions on shared servers (srcf), especially the google api authorization
  * That's it!
  
## How to use
* Share the balloting spreadsheet to `gdoc-editor@thjcr-ballot-system.iam.gserviceaccount.com`
* The `backend/config/config.json` file is manipulated by an administrator, approved by setting CRSIDs in the .htaccess in backend/
* Start a screen/tmux session
* run  `sourceb bin/activate`
* Run with `python backend/document_updater.py` which consumes the config file and creates a directory for the year/name defined in the configuration

* If the ballot goolge doc is not available yet, set the "only_init" flag in `config.json` to true
