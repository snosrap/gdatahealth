SERVER=http://localhost:8087
EMAIL=test@example.com
PASSWORD=test
PROFILE=test@example.com

ATOMTYPE="Content-Type: application/atom+xml"
TEXTTYPE="Content-Type: text/plain"

# Login
AUTH=`curl --silent --data "Email=$EMAIL&Passwd=$PASSWORD&service=health" "$SERVER/accounts/ClientLogin" | grep Auth | cut -d'=' -f2`
HEADER="Authorization: GoogleLogin auth=$AUTH"

#### List ####

# List Profiles
LIST=`curl --silent --header "$HEADER" "$SERVER/health/feeds/profile/list"`

# Find ProfileId for $PROFILE
PROFILEID=`echo $LIST | xpath "/feed/entry[title/text()='$PROFILE']/content/text()"`

#### UI ####

# List Entries
HEALTH=`curl --silent --header "$HEADER" --request GET "$SERVER/health/feeds/profile/ui/$PROFILEID"`

# Create Entry: Problem
H1=`curl --silent --header "$HEADER" --request POST --data-binary "@files/entry_problem_AorticValve.xml" --header "$ATOMTYPE" "$SERVER/health/feeds/profile/ui/$PROFILEID" | xpath "/entry/id/text()"`

# Create Entry: Medication
H2=`curl --silent --header "$HEADER" --request POST --data-binary "@files/entry_medication_Tizan.xml" --header "$ATOMTYPE" "$SERVER/health/feeds/profile/ui/$PROFILEID" | xpath "/entry/id/text()"`

# Delete Entries
curl --silent --header "$HEADER" --request DELETE "$H1"
curl --silent --header "$HEADER" --request DELETE "$H2"

#### Extra ####

# Create Entry: File
F1=`curl --silent --header "$HEADER" --request PUT --data-binary "@files/file_data.txt" --header "$TEXTTYPE" --header "Slug: Text" "http://localhost:8086/health/feeds/profile/ui/$PROFILEID/files"`
F2=`curl --silent --header "$HEADER" --request PUT --data-binary "@files/file_multipart.mime" --header "Content-Type: multipart/related; boundary=\"END_OF_PART\"" --header "Slug: Ignored" "http://localhost:8086/health/feeds/profile/ui/$PROFILEID/files"`
F3=`curl --silent --header "$HEADER" --request PUT --data-binary "@files/file_favicon.png" --header "Content-Type: image/png" --header "Slug: New Png" "http://localhost:8086/health/feeds/profile/ui/$PROFILEID/files"`

# Delete Entry: File
curl --silent --header "$HEADER" --request DELETE "$F1"
curl --silent --header "$HEADER" --request DELETE "$F2"
curl --silent --header "$HEADER" --request DELETE "$F3"

# Create Entry: Profile
P1=`curl --silent --header "$HEADER" --request POST --data-binary "@files/entry_profile.xml" --header "$ATOMTYPE" "$SERVER/health/feeds/profile/list" | xpath "/entry/id/text()"`

# Delete Entry: Profile
curl --silent --header "$HEADER" --request DELETE "$P1"