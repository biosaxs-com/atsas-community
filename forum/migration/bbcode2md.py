#
# phpBB bbcode is almost similar to HTML, but not quite.
# Still the HTMLParser can deal with it.
#

from html.parser import HTMLParser
import datetime


import database

class token:
  def __init__(self):
    self.tokens = []

  def toMarkdown(self):
    markdown = ''
    for token in self.tokens:
      markdown += token.toMarkdown()
    return markdown

  def normalize(self, text):
    # Replacing '<' and '>' here will destroy any '<a id=""></a>' inserted
    # earlier.
    return ' '.join(text.split())


class token_ignore(token):
  def toMarkdown(self):
    return ''


class token_text(token):
  def __init__(self, text):
    token.__init__(self)
    self.text = text

  def toMarkdown(self):
    return self.text


class token_b(token):
  def toMarkdown(self):
    return '**' + token.toMarkdown(self) + "**"


class token_i(token):
  def toMarkdown(self):
    return '*' + token.toMarkdown(self) + "*"


class token_img(token):
  def __init__(self, url, alt):
    token.__init__(self)
    self.url = url
    self.alt = alt

  def toMarkdown(self):
    return '![{}]({} "{}")'.format(self.alt, self.url, self.alt)


class token_li(token):
  def __init__(self, indent):
    token.__init__(self)
    self.indent = indent

  def toMarkdown(self):
    return '\n' + ' ' * self.indent + '- ' + token.toMarkdown(self)


class token_list(token):
  pass

class token_pre(token):
  def toMarkdown(self):
    return '```\n' + token.toMarkdown(self) + '\n```\n'


class token_quote(token):
  def __init__(self, author):
    token.__init__(self)
    self.author = author

  def toMarkdown(self):
    md = ''
    if self.author:
      md += "\n" + self.author + " wrote\n"
    md += "> " + token.toMarkdown(self).replace("\n", "\n> ") + "\n\n"
    return md


# <r> is a custom token. Seen so far to start a post?
class token_r(token):
  def toMarkdown(self):
    markdown = ''
    for t in self.tokens:
      text = t.toMarkdown()
      # print(f">>> {t}: '{text}': '{markdown}'")
      if text:
        if len(markdown) == 0 or markdown[-1] == '\n' or text[0] == '.' or text[0] == ',' or text[0] == '\n':
          markdown += text
        else:
          markdown += ' ' + text
    # markdown = token.normalize(self, markdown)

    return markdown # '\n'.join(textwrap.wrap(markdown, width=80)) + '\n'

# <t> is a custom token. Seen so far to start a post?
class token_t(token):
  def toMarkdown(self):
    markdown = ''
    for t in self.tokens:
      text = t.toMarkdown()
      # print(f">>> {t}: '{text}': '{markdown}'")
      if text:
        if len(markdown) == 0 or markdown[-1] == '\n' or text[0] == '.' or text[0] == ',' or text[0] == '\n':
          markdown += text
        else:
          markdown += ' ' + text
    # markdown = token.normalize(self, markdown)

    return markdown # '\n'.join(textwrap.wrap(markdown, width=80)) + '\n'


class token_url(token):
  def __init__(self, url):
    token.__init__(self)
    self.url = url

  def toMarkdown(self):
    return '[{}]({})'.format(token.toMarkdown(self).strip(), self.url)


class parser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self, convert_charrefs=False)
    self.document = token()
    self.stack = [ self.document ]
    self.indent = 0
    self.bbcode = False
    self.email = False

  def verify_top(self, token):
    if type(self.top()) != type(token):
      raise RuntimeError('sequence error: expected "{}", top is: "{}"'.format(type(token), type(self.top())))

  def top(self):
    return self.stack[-1]

  def push(self, token):
    # Add the token to the currently active list.
    self.top().tokens.append(token)

    # Make this token the currently active one
    self.stack.append(token)

  def pop(self):
    # Remove the topmost token and continue with previous one.
    token = self.stack.pop()

  def query(self, db, post_id):
    rows = database.query(db, f"SELECT poster_id,post_time,post_text FROM phpbb3_posts WHERE post_id == {post_id}")
    assert(len(rows) == 1)  # otherwise: duplicate post_id
    poster_id, post_time, post_text = rows[0]

    rows = database.query(db, f"SELECT username FROM phpbb3_users WHERE user_id=={poster_id}")
    assert(len(rows) == 1)  # otherwise: duplicate post_id
    username, = rows[0]

    print("-- bbcode --")
    print(post_text)

    self.db = db
    self.post_id = post_id
    self.top().tokens.append(token_text('On {}, user {} wrote:\n'.format(datetime.datetime.fromtimestamp(post_time), username)))
    self.feed(post_text)
    
    attachments = database.query(self.db, f"SELECT physical_filename,extension,attach_comment FROM phpbb3_attachments WHERE post_msg_id=={self.post_id}")
    if len(attachments) > 0:
      self.top().tokens.append(token_text("\nAttachments:"))
      self.push(token_list())
      for physical_filename,extension,attach_comment in attachments:
        if not physical_filename.endswith(extension):
          physical_filename = f"{physical_filename}.{extension}"
        src = f"https://github.com/biosaxs-com/atsas-community/blob/saxier-org/forum/attachments/{physical_filename}"
        self.push(token_li(2))
        self.push(token_url(src))
        self.top().tokens.append(token_text(attach_comment if attach_comment else physical_filename))
        self.verify_top(token_url(None))
        self.pop()
        self.verify_top(token_li(0))
        self.pop()
      self.verify_top(token_list())
      self.pop()

  def handle_starttag(self, tag, attrs):
    attrs = dict(attrs)

    if tag == 'attachment':
      filename = attrs['filename']
      # I wouldn't believe it if it weren't in the dump files ...
      filename = filename.replace("&", "&amp;")

      rows = database.query(self.db, f"SELECT physical_filename,attach_comment,extension FROM phpbb3_attachments WHERE post_msg_id=={self.post_id} AND real_filename=='{filename}'")
      # There is at least one person who attached the same file twice to the same post. Errr. Sure.
      # assert(len(rows) == 1)
      print(f"SELECT physical_filename,attach_comment,extension FROM phpbb3_attachments WHERE post_msg_id=={self.post_id} AND real_filename=='{filename}'")
      print(rows)
      physical_filename,attach_comment,extension = rows[0]
      if not physical_filename.endswith(extension):
        physical_filename = f"{physical_filename}.{extension}"
      src = f"https://github.com/biosaxs-com/atsas-community/blob/saxier-org/forum/attachments/{physical_filename}"
      if extension == "gif" or extension == "jpg" or extension == "png":
        self.push(token_img(src + "?raw=true", attach_comment if attach_comment else physical_filename))
      elif    extension == "dat" \
           or extension == "fit" \
           or extension == "log" \
           or extension == "pdb" \
           or extension == "pdf" \
           or extension == "seq" \
           or extension == "txt":
        self.push(token_url(src))
      else:
        raise RuntimeError(f"unhandled attachment extension: {extension}")
 
    elif tag == 'b':
      self.push(token_b())
    elif tag == 'br':
      self.top().tokens.append(token_text('\n'))
    elif tag == 'code':
      self.push(token_pre())
    elif tag == 'color':
      # No color formatting in markdown.
      pass
    elif tag == 'e':
      # The <e> tag marks the end of a BBcode entry.
      self.bbcode = True
    elif tag == 'email':
      # email text/address will still be printed
      self.email = True
    elif tag == 'i':
      self.push(token_i())
    elif tag == 'img':
      self.push(token_img(attrs['src'], attrs['alt'] if 'alt' in attrs else ''))
    elif tag == 'li':
      self.push(token_li(self.indent))
    elif tag == 'list':
      self.indent += 2
      self.push(token_list())
    elif tag == 'link_text':
      # an elided version of the text, can be ignored (not a bbcode, but easier)
      self.bbcode = True
    elif tag == 'quote':
      self.push(token_quote(attrs['author'] if 'author' in attrs else ''))
    elif tag == 'r':
      self.push(token_r())
    elif tag == 's':
      # The <s> tag marks the begin of a BBcode entry.
      self.bbcode = True
    elif tag == 'size':
      # No size formatting in markdown.
      pass
    elif tag == 'sub':
      self.top().tokens.append(token_text('<sub>'))
    elif tag == 'sup':
      self.top().tokens.append(token_text('<sup>'))
    elif tag == 't':
      self.push(token_t())
    elif tag == 'u':
      # No underline in markdown.
      pass
    elif tag == 'url':
      self.push(token_url(attrs['url']))
    else:
      raise RuntimeError(f"unhandled start tag: {tag}")

  def handle_endtag(self, tag):
    if tag == 'attachment':
      # skip verify, can be either 'img' or 'url'
      self.pop()
    elif tag == 'b':
      self.verify_top(token_b())
      self.pop()
    elif tag == 'br':
      pass
    elif tag == 'code':
      self.verify_top(token_pre())
      self.pop()
    elif tag == 'color':
      # No color formatting in markdown.
      pass
    elif tag == 'e':
      # The </e> tag marks the end of a BBcode entry.
      self.bbcode = False
    elif tag == 'email':
      # email text/address will still be printed
      self.email = False
    elif tag == 'i':
      self.verify_top(token_i())
      self.pop()
    elif tag == 'img':
      self.verify_top(token_img(None, None))
      self.pop()
    elif tag == 'link_text':
      # an elided version of the text, can be ignored (not a bbcode, but easier)
      self.bbcode = False
    elif tag == 'li':
      self.verify_top(token_li(0))
      self.pop()
    elif tag == 'list':
      self.indent -= 2
      self.verify_top(token_list())
      self.pop()
    elif tag == 'quote':
      self.verify_top(token_quote(None))
      self.pop()
    elif tag == 'r':
      self.verify_top(token_r())
      self.pop()
    elif tag == 's':
      # The </s> tag marks the end of a BBcode entry.
      self.bbcode = False
    elif tag == 'size':
      # No size formatting in markdown.
      pass
    elif tag == 'sub':
      self.top().tokens.append(token_text('</sub>'))
    elif tag == 'sup':
      self.top().tokens.append(token_text('</sup>'))
    elif tag == 't':
      self.verify_top(token_t())
      self.pop()
    elif tag == 'u':
      # No underline in markdown.
      pass
    elif tag == 'url':
      self.verify_top(token_url(None))
      self.pop()
    else:
      raise RuntimeError(f"unhandled end tag: {tag}")

  def handle_data(self, data):
    if self.email:
      self.top().tokens.append(token_text("email address removed for privay reasons"))
    elif not self.bbcode:
      # Normalize whitespace, remove newlines, remove leading and trailing whitespace.
      # But no good if we are in a preformatted section.
      # data = ' '.join(data.split())

      # Only removed leading and trailing whitespace.
      if data.strip():
       if type(self.top()) == type(token_pre()):
         self.top().tokens.append(token_text(data))
       else:
         # self.top().tokens.append(token_text(data.strip().replace('<', '\<').replace('>', '\>')))
         self.top().tokens.append(token_text(data.strip()))

  def handle_entityref(self, name):
    is_pre = type(self.top()) == type(token_pre())
  
    if name == 'amp':
      self.top().tokens.append(token_text('&'))
    elif name == 'gt':
      if is_pre:
        self.top().tokens.append(token_text('>'))
      else:
        self.top().tokens.append(token_text('\>'))
    elif name == 'lt':
      if is_pre:
        self.top().tokens.append(token_text('<'))
      else:
        self.top().tokens.append(token_text('\<'))
    else:
      raise RuntimeError(f"unhandled entityref: {name}")

  def handle_charref(self, name):      
    if name == '120143':                                  # A math X (twitter)
      self.top().tokens.append(token_text('X'))
    else:
      raise RuntimeError(f"unhandled charref: {name}")

  def toMarkdown(self):
    markdown = []
    for token in self.document.tokens:
      markdown.append(token.toMarkdown())
    return '\n'.join(markdown)

