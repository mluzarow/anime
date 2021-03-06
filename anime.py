#region Dependencies
import argparse
from bs4 import BeautifulSoup
import httplib
import logging
import os
from random import randint
import re
import urllib2
#endregion Dependencies

#region Defines
MIN_ID=1
MAX_ID=11000
MAX_RECOMMENDATIONS = 3
PATH = 'anime - History'
ANN_PATH = 'http://cdn.animenewsnetwork.com/encyclopedia/api.xml?title='
#endregion Defines

################################################################################
## anime.py
##
## Console application will take very anime arguments and recommend up to 3
## very anime recommendations. Uses ANN API.
################################################################################

# Stores the meat of the anime
class Anime(object):
    def __init__ (self, id, title, weightedMean=None, isManga=False, isTV=False, isOVA=False, isMovie=False):
        self.id = id
        self.title = title
        self.weightedMean = weightedMean
        self.isManga = isManga
        self.isTV = isTV
        self.isOVA = isOVA
        self.isMovie = isMovie

    def validRating(self, min, max):
        # If there is not specified rating, it is not valid
        if not self.weightedMean:
            return False
        # True only if both means are between [min, max]
        return (self.weightedMean >= min and self.weightedMean <= max)

# Returns the Anime object represented by the anime id as per
# Anime News Network (ANN).
def getAnime(animeId):
    url = ANN_PATH + str(animeId)

    try: 
        # Follow URL
        response = urllib2.urlopen(url)
        # Get HTML page data
        html = response.read()
        # Spruce up the soup
        parsedHtml = BeautifulSoup(html, "lxml")

        # Get tags <anime> and <manga>
        parsedAnime = parsedHtml.find ("anime")
        parsedManga = parsedHtml.find ("manga")

        # Check if the <anime> tag exists on the page
        if parsedAnime is None:
            # Anime tag does not exist, so check for the <manga> tag instead
            if parsedManga is None:
                # Neither tag exists, so the ID must be a dead end
                return (None)
            # <manga> tags exists, find attributes of <manga>
            else:
                title = parsedManga ["name"]
                itemType = parsedManga ["type"]
        # <anime> tag exists, find attributes of <anime>
        else:
            # Check if the first tag after <ann> is anime or manga; if anime is not found, it has to be manga
            title = parsedAnime ["name"]
            itemType = parsedAnime ["type"]

        if itemType == "manga":
            isManga = True
            isTV = False
            isOVA = False
            isMovie = False
        elif itemType == "TV":
            isManga = False
            isTV = True
            isOVA = False
            isMovie = False
        elif itemType == "OVA":
            isManga = False
            isTV = False
            isOVA = True
            isMovie = False
        else:
            isManga = False
            isTV = False
            isOVA = False
            isMovie = True

        # Get tag <ratings>
        parsedRatings = parsedHtml.find ("ratings")

        # Check if tag <ratings> exists
        if parsedRatings is None:
            # Does not exist, so there are no ratings
            ratingText = None     
        # Tag exists  
        else:
            # Get attribute
            ratingText =  parsedRatings ['nb_votes']

        # Check if rating is specified.
        if ratingText is None:
            # Rating is not specified, so don't include it
            return Anime(id=animeId, title=title, isManga=isManga, isTV=isTV, isOVA=isOVA, isMovie=isMovie)
        # Rating is specified, so include it
        weightedMean = float(ratingText)

        return Anime(animeId, title, weightedMean, isManga, isTV, isOVA, isMovie)

    except urllib2.HTTPError, e:
        logging.warning('HTTPError=%s, animeId=%s' % (str(e.code), str(animeId)))
    except urllib2.URLError, e:
        logging.warning('URLError=%s, animeId=%s' % (str(e.reason), str(animeId)))
    except httplib.HTTPException, e:
        logging.warning('HTTPException, animeId=%s' % str(animeId))
    except Exception:
        import traceback
        logging.warning('generic exception: ' + traceback.format_exc())

def readHistory (path):
    temp = list ()

    pathFile = path + '/History.txt'

    # Check if the directiory exists
    if (not os.path.exists (path)):
        # It does not exist, so create it
        os.makedirs (path)

    # Check if the file exists
    if (not os.path.isfile (pathFile)):
        # File does not exist, so make it
        with open (pathFile, 'w') as f:
            f.write ('0')
        f.closed

    # Open History and read in all IDs
    with open (pathFile, 'r') as f:
        for ID in f:
            temp.append (ID.split('\n')[0])
    f.closed

    return (temp)

def writeHistory (path, oldIDs):
    pathFile = path + '/History.txt'

    # Check if the directiory exists
    if (not os.path.exists (path)):
        # It does not exist, so create it
        os.makedirs (path)

    # Check if the file exists
    if (not os.path.isfile (pathFile)):
        # File does not exist, so make it
        with open (pathFile, 'w') as f:
            f.write ('0')
        f.closed

    # Open History and write all the values in there (overwriting everything)
    with open (pathFile, 'w') as f:
        for ID in oldIDs:
            f.write (str(ID) + '\n')
    f.closed

# Returns a random Integer between |MIN_ID| and |MAX_ID|, both inclusive.
def getRandomID():
    return randint(MIN_ID, MAX_ID)

############################ MAIN IS RIGHT HERE ################################
#region Main

# Set up argument parser
parser = argparse.ArgumentParser()
parser.add_argument('--min_rating', dest = 'min', type = float,  default = 0.0,
                    help="Minimum allowed rating as per AnimeNewsNetwork (ANN)")
parser.add_argument ('--max_rating', dest = 'max', type = float, default = 10.0,
                     help = "Maximim allowed rating as per AnimeNewsNetwork (ANN)")
parser.add_argument ('--recommendations', dest = 'recs', type = int, default = 1,
                     help = 'Number of recommendations the program will generate')
parser.add_argument ('--exclude_manga', dest='manga', action='store_false', default=True,
                      help='Remove manga from the recommendations')
parser.add_argument ('--exclude_TV', dest = 'TV', action = 'store_false', default = True,
                     help = "Remove TV anime (including specials) from the recommendations")
parser.add_argument ('--exclude_OVA', dest = 'OVA', action = 'store_false', default = True,
                     help = "Remove OVAs from the recommendations")
parser.add_argument ('--exclude_movie', dest = 'movie', action = 'store_false', default = True,
                     help = "Remove movies from the recommendations")

# args = parser.parse_args(['--recommendations', '3', "--exclude_manga"])

# Do not allow more than MAX_RECOMMENDATIONS recs
if (args.recs > MAX_RECOMMENDATIONS):
    args.recs = MAX_RECOMMENDATIONS

print ('===========SETTINGS===========')
print ('Recommendations:  %s' % args.recs)
print ('Minimum Rating:   %s' % args.min)
print ('Maximum Rating:   %s' % args.max)
print ('Include Manga:    %s' % args.manga)
print ('Include TV Shows: %s' % args.TV)
print ('Include OVAs:     %s' % args.OVA)
print ('Include movies:   %s' % args.movie)

# Read in all former used IDs
oldIDs = readHistory (PATH)
# Makes a list for all IDs used in this run of the program
runIDs = list ()
# Makes a list of all the to-be-recommended animes
animes = list()
# Loop var
count = 0
# Flag for getting IDs
getID = True
# Number of rejected animes during the currnet recommendation search
totalRejects = 0
print ("\n===SEARCHING FOR THE ANIMES===")

# Loop while under the requested amount of recommendations
while (count < args.recs):
    # Get an ANN ID
    while (getID):
        # Get random ANN ID 
        animeId = getRandomID() 

        # Check that this ID was not already generated this run
        for ID in runIDs:
            # Found an old ID; go back and get a new ID
            if (animeId == ID):
                getID = False
        # Check that this ID was not already used in a prior recommendation
        for ID in oldIDs:
            if (animeId == ID):
                getID = False
        
        # getID is False, so the ID is old; get a new ID (keep loop going with getID = True)
        if (getID == False):
            getID = True
        # getID is True, so the ID is NOT old; break out of the loop and continue
        else:
            # Did not find any old ID matches
            getID = False
    
    # Save our ID in runIDs as it is going to be used this run
    runIDs.append(animeId)

    # Get very anime information from ANN
    anime = getAnime(animeId)

    # There is no ANN entry with the given ID; 
    if anime is None:
        # Log ID in usedID and try again
        oldIDs.append(animeId)
        getID = True
    # If new ID is not requested
    if (not getID):
        # If the ID pointed to a manga
        if anime.isManga:
            # Check if user is ok with manga
            if not args.manga:
                # Prints that the anime was rejected so that the user sees that something is going on
                totalRejects += 1
                print ("Rejected : %d\r" % totalRejects),
                # User is not ok; Log ID in usedID and try again
                getID = True
    # If new ID is not requested
    if (not getID):
        # If the ID pointed to a TV series
        if anime.isTV:
            # Check if user is ok with TV series
            if not args.TV:
                # Prints that the anime was rejected so that the user sees that something is going on
                totalRejects += 1
                print ("Rejected : %d\r" % totalRejects),
                # User is not ok; Log ID in usedID and try again
                getID = True
    # If new ID is not requested
    if (not getID):
        # If the ID pointed to a OVAs
        if anime.isOVA:
            # Check if user is ok with OVAs
            if not args.OVA:
                # Prints that the anime was rejected so that the user sees that something is going on
                totalRejects += 1
                print ("Rejected : %d\r" % totalRejects),
                # User is not ok; Log ID in usedID and try again
                getID = True
    # If new ID is not requested
    if (not getID):
        # If the ID pointed to a movie
        if anime.isMovie:
            # Check if user is ok with movies
            if not args.movie:
                # Prints that the anime was rejected so that the user sees that something is going on
                totalRejects += 1
                print ("Rejected : %d\r" % totalRejects),
                # User is not ok; Log ID in usedID and try again
                getID = True
    # If new ID is not requested
    if (not getID):
         # If the ID pointed to an item with an invalid rating
        if not anime.validRating(args.min, args.max):
            # Prints that the anime was rejected so that the user sees that something is going on
            totalRejects += 1
            print ("Rejected : %d\r" % totalRejects),
            # Log ID in usedID and try again
            getID = True
    # Only increment if there was no premature new ID request
    if (not getID):
        print ("FOUND [%d of %d]" % (count + 1, args.recs))
        totalRejects = 0
        # Adds the current ID to oldIDs as the user has had it recommended to them
        oldIDs.append (animeId)
        animes.append (anime)
        getID = True
        # Loop var
        count+=1

print("\n......................................................");
print("               ***SUGGESTIONS***");
print("......................................................");

writeHistory(PATH, oldIDs)

for anime in animes:
    print (anime.title.encode('utf-8'))

#endregion Main
