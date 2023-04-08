#!/bin/bash

TOKEN=$1
BASEURL="http://public-806548633.us-east-1.elb.amazonaws.com/"

listplayouts()
{
    URLPATH="api/playout/" 
    curl --location --request GET "${BASEURL}${URLPATH}" --header "Authorization: token $TOKEN"
}

listassets()
{
    URLPATH="api/vod_asset/" 
    curl --location --request GET "${BASEURL}${URLPATH}" --header "Authorization: token $TOKEN"
}

create_playout()
{
    ## Create Playout
    URLPATH="api/playout/" 
    RES=$(curl --location --request POST "${BASEURL}${URLPATH}" --header "Authorization: token $TOKEN" --header 'Content-Type: application/json' --data-raw '{"resolution": "UHD"}')
    #RES='{"resolution":"UHD","id":"f6230532-be9a-4e27-8375-202c45b4892d","status":"","created_on":"2022-12-02T03:47:17.895486Z","distribution":null}'
    echo $RES
    PLAYOUTID=`echo ${RES} | jq -r '.id'`
    echo "PLAYOUT IS: $PLAYOUTID"
}

getpresignedkey()
{
    URLPATH="api/raw_video/" 
    RES=$(curl --location --request POST "${BASEURL}${URLPATH}" --header "Authorization: token $TOKEN" --header 'Content-Type: application/json' --data-raw "{\"playout\": \"$PLAYOUTID\"}")
    echo "Signing key is $RES"
    S3URL=`echo ${RES} | jq -r '.url'`
    ACCESSKEY=`echo ${RES} | jq -r '.fields.AWSAccessKeyId'`
    SIGNATURE=`echo ${RES} | jq -r '.fields.signature'`
    SECURITY_TOKEN=`echo ${RES} | jq -r '.fields["x-amz-security-token"]'`
    KEY=`echo ${RES} | jq -r '.fields.key'`
    POLICY=`echo ${RES} | jq -r '.fields.policy'`
}

uploadwithpresignedkey()
{
    VIDOFILE="./video.mp4"
    curl --location --request POST "${S3URL}" --form "key=\"$PLAYOUTID\"" --form "AWSAccessKeyId=\"${ACCESSKEY}\"" --form "policy=\"${POLICY}\"" --form "signature=\"${SIGNATURE}\"" --form "x-amz-meta-asset-id=\"${ASSETID}\"" --form "file=@\"${VIDOFILE}\""
}

configure_static_input()
{
    URL_TO_MP4=$1
    URLPATH="api/input/"
    RES=$(curl --location --request POST "${BASEURL}${URLPATH}" --header "Authorization: token $TOKEN" --header 'Content-Type: application/json' --data-raw "{\"playout_id\": \"${PLAYOUTID}\", \"input_type\": \"static\", \"s3_url\": \"${URL_TO_MP4}\"}")
    echo "Static input is: $RES"
    INPUTID=`echo ${RES} | jq -r '.id'`
}

turn_on_receiver_for_live_video()
{
    URLPATH="api/input/"
    curl --location --request PATCH "${BASEURL}${URLPATH}${PLAYOUTID}/" --header "Authorization: token $TOKEN" --header 'Content-Type: application/json' --data-raw "{\"input_id\": \"${INPUTID}\", \"state\": \"on\"}"
}

turn_on_channel()
{
    URLPATH="api/channel/"
    curl --location --request PATCH "${BASEURL}${URLPATH}${PLAYOUTID}/" --header "Authorization: token $TOKEN" --header 'Content-Type: application/json' --data-raw "{\"state\": \"on\"}"
}

turn_off_channel()
{
    URLPATH="api/channel/"
    curl --location --request PATCH "${BASEURL}${URLPATH}${PLAYOUTID}/" --header "Authorization: token $TOKEN" --header 'Content-Type: application/json' --data-raw "{\"state\": \"off\"}"
}

turn_off_receiver_for_live_video()
{
    URLPATH="api/input/"
    curl --location --request POST "${BASEURL}${URLPATH}${PLAYOUTID}/" --header "Authorization: token $TOKEN" --header 'Content-Type: application/json' --data-raw "{\"input_id\": \"${INPUTID}\", \"state\": \"off\"}"
}

switch_input()
{
    INPUTID=$1
    URLPATH="api/action/"
    curl --location --request POST "${BASEURL}${URLPATH}" --header "Authorization: token $TOKEN" --header 'Content-Type: application/json' --data-raw "{\"playout_id\": \"${PLAYOUTID}\", \"action_type\": \"input switch\", \"start_type\": \"immediate\", \"input_attachment\": \"${INPUTID}\"}"
}


############
#  VEEPS LEARNS OF A NEW CONCERT 
#  Timeframe - Day or weeks before concert 
############
if false
then
    create_playout
    read -p "Press any key to continue - playout"

    configure_static_input "s3://veeps-triumph-videoshare/video1.mp4"
    INPUTID_1=$INPUTID

    read -p "Press any key to continue - static_asset 1"

    configure_static_input "s3://veeps-triumph-videoshare/video3.mp4"
    INPUTID_2=$INPUTID

    read -p "Press any key to continue - static_asset 2"
fi 
############
#  Concert 
#  Start up to 30 minutes before show 
############

#turn_on_receiver_for_live_video $INPUTID_3
#read -p "Press any key to continue - flow on"

if true
then
    PLAYOUTID="f6230532-be9a-4e27-8375-202c45b4892d"
    INPUTID_1="ddd65b07-60f0-445b-956c-88eae16f9570"
    INPUTID_2="9fe58fbf-13f3-46ee-befa-f6e4611c95d2"
fi 
#Cue up video 2 as first input 
switch_input $INPUTID_2

turn_on_channel
read -p "Press any key to continue - channel on"

#get_distribution_url

switch_input $INPUTID_1

read -p "Press any key to continue - switch input 1"

switch_input $INPUTID_2

read -p "Press any key to continue - switch input 2"

switch_input $INPUTID_1

read -p "Press any key to continue - switch input 1"

turn_off_channel
read -p "Press any key to continue - channel off"

#turn_off_receiver_for_live_video $INPUTID_3
#read -p "Press any key to continue - flow off"

#clipping

###########
#  Cleanup 
#  When all clipping is done, livestream is done 
###########

#delte_playout