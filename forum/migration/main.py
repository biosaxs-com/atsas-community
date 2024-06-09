#
# Still TODO for this script:
#   [x] update/redirect links to the ATSAS download page to biosaxs.com
#   [x] set the 'saxier-org' label for new discsussions
#
# Prerequisites:
#   [x] make at least some manuals public to ensure that everything works
#
# General Setup:
#   [x] create a 'saxier.org' bot account for submission
#   [x] create a personal acess token for the saxier bot
#   [ ] create Discussion Categories identical to those at saxier.org
#   [ ] make atsas-community public so the bot account can submit stuff
#   [ ] add 'write' permissions the saxier.org bot for atsas-community
#
# Specific Setup:
#   [ ] verify the GitHub manual URL
#   [ ] set 'repository-owner', and 'repository-name' in github.py
#   [ ] set the personal access token
#


import database
import bbcode2md
import github

import time
import re
from urllib.parse import urlparse, parse_qs
from html import unescape

# Unique repository ID at GitHub.
github_repository_id = github.get_repository_id()

# Maps saxier forum ID to GitHub discussion category ID.
github_discussion_categories = {}
github_discussion_category_url = {}

# Dictionary to map saxier topic_id to GitHub discussion ID and URL.
github_discussions_id = {}
github_discussions_url = {}

# Dictionary to map saxier post_id to GitHub comment URL.
github_comments_url = {}



def updateForumUrl(match):
  # there is at least one genius who put in a questionable url
  print(match.group(0))
  url = urlparse(unescape(match.group(0)))
  print(url)
  query = parse_qs(url.query)
  forum_id = query['f'][0]

  return github_discussion_category_url[forum_id]


def updateTopicUrl(match):
  # there is at least one genius who put in a questionable url
  url = urlparse(unescape(match.group(0)))
  query = parse_qs(url.query)

  topic_id = query['t'][0] if 't' in query.keys() else None
  post_id = query['p'][0] if 'p' in query.keys() else None
  if not post_id and url.fragment:
    post_id = url.fragment.replace("p", "")

  if post_id:
    if post_id in github_comments_url:
      return github_comments_url[post_id]
    else:    
      print(f"error: edited comment, post_id {post_id} is in the future")
      return ""
  else:
    if topic_id in github_discussions_url:
      return github_discussions_url[topic_id]
    else:    
      print(f"error: edited comment, topic_id {topic_id} is in the future")
      return ""


def updateManualUrl(match):
  url = urlparse(unescape(match.group(0)))

  components = url.path.split('/')
  newUrl = "https://biosaxs-com.github.io/atsas/latest/manuals/" + components[-1].replace("manual_", "")
  if url.fragment:
    newUrl += "#" + url.fragment

  return newUrl



def updateUrls(text):
  # Regular expression to match forum links.
  text = re.sub(r"https?://www.saxier.org//?forum/viewforum.php\?f=([0-9]+)", updateForumUrl, text);

  # Regular expression to match forum post links.
  text = re.sub(r"https?://www.saxier.org//?forum/viewtopic.php\?([tfp]=[0-9]+)(&[ftp]=[0-9]+)*(#p[0-9]+)?", updateTopicUrl, text)
 
  # Regular expression to match the ATSAS install page. (FIXME: correct link?)
  text = re.sub(r"https?://www.embl-hamburg.de/\S*/install.html(#\S+)?", "https://biosaxs-com.github.io/atsas/latest/install/", text)

  # Regular expression to match the ATSAS download page.
  text = re.sub(r"https?://www.embl-hamburg.de/\S*/download.html", "https://www.biosaxs.com/download", text)

  # ATSAS online links
  text = re.sub(r"https?://www.embl-hamburg.de/\S*/atsas-online", "https://www.embl-hamburg.de/biosaxs/atsas-online/", text)

  # Regular expression to match links to application manuals.
  applications = [ "almerge", "alpraxin", "autorg", "bilmix", "bodies", "bunch", "chromixs", "cifop", "cifsup", "coral", "crysol", "crysol3", "cryson", "dam2is", "damaver", "damclust", "dammif", "dammin", "dara", "dattools", "datadjust", "databsolute", "databsmw", "dataver", "datcmp", "datcrop", "datmerge", "datop", "datporod", "datregrid", "datrg", "datclass", "datshanum", "elllip", "em2dam", "eom", "ffmaker", "flexbin", "glycosylation", "globsymm", "gnom", "gasbor", "imsim", "im2dat", "lipmix", "mixture", "monsa", "nmator", "oligomer", "parcoor", "polysas", "primus", "primus-qw", "sasdoc", "saspy", "sasref", "sasres", "secplot", "shanum", "sreflex", "supalm", "supcomb", "svdplot" ]
  for app in applications:
    text = re.sub(r"https?://www.embl-hamburg.de/\S*(" + app + ".s?html)(#\S+)?", updateManualUrl, text);

  return text



# The local sqlite database.
db = database.connect("/Users/franke/saxier/saxier_backup.sqlite")

#
# Get the list of all saxier forums and the list of all GitHub discussion categories.
# Match them up.
# NOTE: There are more saxier forums than GitHub categories (forum 14 is private)
#
forums = database.query(db, "SELECT forum_id,forum_name FROM phpbb3_forums")
# Convert list of tuples to dictionary.
tmp = {}
for forum_id, forum_name in forums:
  if forum_id != 14 and forum_id != 20:
    forum_name = forum_name.replace("&amp;", "&")
    tmp[forum_name] = str(forum_id)
forums = tmp

# Comes as dictionary.
categories = github.get_discussion_categories()

# Match by name.
for category_name in categories.keys():
  if category_name in forums.keys():
    normalized_category_name = category_name.lower().replace('&', '').replace('/', ' ').replace('  ', ' ').replace(' ', '-')
    github_discussion_category_url[forums[category_name]] = f"https://github.com/biosaxs-com/atsas-community/discussions/categories/{normalized_category_name}"
    github_discussion_categories[forums[category_name]] = categories[category_name]
  else:
    print(f"warning: no such category '{category_name}' in '{forums}'")


for key in github_discussion_categories.keys():
  print(f"{key}: {github_discussion_categories[key]}, {github_discussion_category_url[key]}")


# Make sure we have a "saxier.org" label.
github_labels = github.get_labels()
if not 'saxier-org' in github_labels:
  github.create_label(github_repository_id, "saxier-org", "5319E7", "Archived from www.saxier.org/forum")
  github_labels = github.get_labels()


#
# We have to iterate over posts to make sure that we process them in chronological order.
# Point being: we want to update cross references between discussions and for that
# we need to have the referenced comment already submitted.
#
# This makes lookups a bit backwards. Iterating forum-topic-post would make this script
# easier to deal with.
#
posts = database.query(db, "SELECT post_id,topic_id,forum_id,post_visibility FROM phpbb3_posts")

for post_id, topic_id, forum_id, post_is_visible in posts:
  if not post_is_visible:
    continue

  # Private EMBL BIOSAXS forums. No idea how to exclude post to this otherwise.
  if forum_id == 14 or forum_id == 20:
    continue

  # Get the topic title.
  rows = database.query(db, f"SELECT topic_title FROM phpbb3_topics WHERE topic_id={topic_id}")
  assert(len(rows) == 1)
  topic_title, = rows[0]

  # Convert BBcode to suitable markdown.
  parser = bbcode2md.parser()
  parser.query(db, post_id)
  comment = parser.toMarkdown()

  # Update cross references to older posts and external links to manuals.
  editedComment = updateUrls(comment)

  # print("-- markdown --")
  # print(comment)
  print("-- edited --")
  print(editedComment)

  if not topic_id in github_discussions_id.keys():
    # Create a new Discussion/Topic.
    github_discussion_id,github_discussion_url = github.create_discussion(github_repository_id, github_discussion_categories[str(forum_id)], topic_title, editedComment)
    github_discussions_id[topic_id]  = github_discussion_id
    github_discussions_url[topic_id] = github_discussion_url
    print(f" >>> new discussion id: '{github_discussion_id}', url: '{github_discussion_url}'")

    time.sleep(2)
    github.add_label(github_discussion_id, github_labels['saxier-org'])

    time.sleep(2)
    github.lock_discussion(github_discussion_id)
  else:
    # Append a Comment/Post to an existing Discussion/Topic.
    github_comment_id, github_comment_url = github.add_comment(github_discussions_id[topic_id], editedComment)
    github_comments_url[post_id] = github_comment_url
    print(f" >>> new comment id: '{github_comment_id}', url: '{github_comment_url}'")

  #
  # To not be told off for hammering the API, wait a bit between requests.
  # Two seconds was not sufficient, neither was 5 seconds:
  #   "Failed to create discussion: [{'type': 'UNPROCESSABLE', 'path': ['createDiscussion'], 'locations': [{'line': 3, 'column': 7}], 'message': 'was submitted too quickly'}]""
  # See
  #   https://github.com/cli/cli/issues/4801
  # and eventually:
  #   https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api#rate-limit
  #
  # -- 8< --
  # Create too much content on GitHub in a short amount of time. In general, no more than 80
  # content-generating requests per minute and no more than 500 content-generating requests
  # per hour are allowed. Some endpoints have lower content creation limits. Content creation
  # limits include actions taken on the GitHub web interface as well as via the REST API and
  # GraphQL API.
  # -- 8< --
  #
  time.sleep(15)
