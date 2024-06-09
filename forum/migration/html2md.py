
import argparse
from html.parser import HTMLParser
from html.entities import name2codepoint
import textwrap


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
  


class token_a_name(token):
  def __init__(self, name):
    token.__init__(self)
    self.name = name

  def toMarkdown(self):
    return '<a id="{}">{}</a>'.format(self.name, token.toMarkdown(self))


class token_a_href(token):
  def __init__(self, url):
    token.__init__(self)
    self.url = url

  def toMarkdown(self):
    return '[{}]({})'.format(token.toMarkdown(self).strip(), self.url)


class token_b(token):
  def toMarkdown(self):
    return '**' + token.toMarkdown(self) + "**"


class token_body(token):
  pass


class token_code(token):
  pass


class token_h1(token):
  def toMarkdown(self):
    return '\n# ' + token.toMarkdown(self) + '\n'


class token_h2(token):
  def toMarkdown(self):
    return '\n## ' + token.toMarkdown(self) + '\n'


class token_h3(token):
  def toMarkdown(self):
    return '\n### ' + token.toMarkdown(self) + '\n'


class token_h4(token):
  def toMarkdown(self):
    return '\n#### ' + token.toMarkdown(self) + '\n'


class token_i(token):
  def toMarkdown(self):
    return '_' + token.toMarkdown(self) + "_"


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


class token_ol(token):
  pass


class token_p(token):
  def toMarkdown(self):
    markdown = ''
    for t in self.tokens:
      text = t.toMarkdown()
      if text[0] == '.' or text[0] == ',':
        markdown += text
      else:
        markdown += ' ' + text
    markdown = token.normalize(self, markdown)

    return '\n'.join(textwrap.wrap(markdown, width=80)) + '\n'


class token_pre(token):
  def toMarkdown(self):
    return '```\n' + token.toMarkdown(self) + '\n```\n'


class token_sub(token):
  def toMarkdown(self):
    return '~' + token.toMarkdown(self) + "~"


class token_sup(token):
  def toMarkdown(self):
    return '^' + token.toMarkdown(self) + "^"


class token_table(token):
  def toMarkdown(self):
    return '\n' + token.toMarkdown(self) + '\n'


class token_td(token):
  def toMarkdown(self):
    # markdown does not handle newlines in table cells;
    # normalize and remove line breaks and excess whitespace
    td = token.normalize(self, token.toMarkdown(self))
    return '| ' + td + ' '


class token_th(token):
  def toMarkdown(self):
    return '| ' + token.toMarkdown(self) + ' '


class token_title(token):
  def toMarkdown(self):
    return ''


class token_tr(token):
  def toMarkdown(self):
    markdown = token.toMarkdown(self) + '|\n';
    # If this is a header row, follow with a special row to separate header and data.
    if type(self.tokens[0]) == type(token_th()):
      markdown += '|----' * len(self.tokens) + '|\n'
    return markdown


class token_tt(token):
  pass


class token_ul(token):
  pass




class manualparser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self, convert_charrefs=False)
    self.document = token()
    self.stack = [ self.document ]
    self.indent = 0

  def verify_top(self, token):
    if type(self.top()) != type(token):
      print('sequence error: {}: expected "{}", top is: "{}"'.format(HTMLParser.getpos(), type(token), type(self.top())))

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



  def handle_starttag(self, tag, attrs):
    # Convert list of tuples to dictionary for easier access.
    attrs = dict(attrs)

    if tag == 'a':
      if 'name' in attrs:
        # anchor
        self.push(token_a_name(attrs['name']))
      elif 'href' in attrs:
        # link
        self.push(token_a_href(attrs['href']))
      else:
        # some manuals have an empty "<a>" tag?!
        self.push(token_ignore())

    elif tag == 'b' or tag == 'strong':
      self.push(token_b())

    elif tag == 'body':
      self.push(token_body())

    elif tag == 'br':
      # A forced, in-place new line.
      self.top().tokens.append(token_text('\n'))

    elif tag == 'code':
      self.push(token_code())

    elif tag == 'div':
      pass

    elif tag == 'dd':
      self.push(token_td())

    elif tag == 'dl':
      # dl: description list
      self.push(token_table())

    elif tag == 'dt':
      self.push(token_tr())
      self.push(token_td())

    elif tag == 'h1':
      self.push(token_h1())

    elif tag == 'h2':
      self.push(token_h2())

    elif tag == 'h3':
      self.push(token_h3())

    elif tag == 'h4':
      self.push(token_h4())

    elif tag == 'h5':
      self.push(token_h4())

    elif tag == 'head':
      pass

    elif tag == 'html':
      pass

    elif tag == 'i' or tag == 'em':
      self.push(token_i())

    elif tag == 'img':
      self.push(token_img(attrs['src'], attrs['alt'] if 'alt' in attrs else ''))
      # there usually is no </img> tag
      self.pop()

    elif tag == 'li':
      self.push(token_li(self.indent))

    elif tag == 'link':
      pass

    elif tag == 'meta':
      pass

    elif tag == 'ol':
      # FIXME: currently there is no difference in output between ol and ul!
      self.indent += 2
      self.push(token_ol())

    elif tag == 'p':
      self.push(token_p())

    elif tag == 'pre':
      self.push(token_pre())

    elif tag == 'small':
      pass

    elif tag == 'span':
      pass

    elif tag == 'style':
      pass

    elif tag == 'sub':
      self.push(token_sub())

    elif tag == 'sup':
      self.push(token_sup())

    elif tag == 'table':
      self.push(token_table())

    elif tag == 'tbody':
      pass

    elif tag == 'td':
      self.push(token_td())

    elif tag == 'th':
      self.push(token_th())

    elif tag == 'title':
      self.push(token_title())

    elif tag == 'tr':
      self.push(token_tr())

    elif tag == 'tt':
      self.push(token_tt())

    elif tag == 'ul':
      self.indent += 2
      self.push(token_ul())

    else:
      print("unhandled start tag: " + tag)


  def handle_endtag(self, tag):
    if tag == 'a':
      self.pop()

    elif tag == 'b' or tag == 'strong':
      self.verify_top(token_b())
      self.pop()

    elif tag == 'body':
      self.verify_top(token_body())
      self.pop()

    elif tag == 'br':
      # A forced, in-place new line.
      self.top().tokens.append(token_text('\n'))

    elif tag == 'code':
      self.verify_top(token_code())
      self.pop()

    elif tag == 'div':
      pass

    elif tag == 'dd':
      self.verify_top(token_td())
      self.pop()         # table data
      self.verify_top(token_tr())
      self.pop()         # table row

    elif tag == 'dl':
      self.pop()

    elif tag == 'dt':
      self.pop()

    elif tag == 'h1':
      self.verify_top(token_h1())
      self.pop()

    elif tag == 'h2':
      self.verify_top(token_h2())
      self.pop()

    elif tag == 'h3':
      self.verify_top(token_h3())
      self.pop()

    elif tag == 'h4':
      self.verify_top(token_h4())
      self.pop()

    elif tag == 'h5':
      self.verify_top(token_h4())
      self.pop()

    elif tag == 'head':
      pass

    elif tag == 'html':
      pass

    elif tag == 'i' or tag == 'em':
      self.verify_top(token_i())
      self.pop()

    elif tag == 'img':
      pass

    elif tag == 'li':
      self.verify_top(token_li(0))
      self.pop()

    elif tag == 'link':
      pass

    elif tag == 'meta':
      pass

    elif tag == 'ol':
      self.verify_top(token_ol())
      self.pop()

    elif tag == 'p':
      self.verify_top(token_p())
      self.pop()

    elif tag == 'pre':
      self.verify_top(token_pre())
      self.pop()

    elif tag == 'small':
      pass

    elif tag == 'span':
      pass

    elif tag == 'style':
      pass

    elif tag == 'sub':
      self.verify_top(token_sub())
      self.pop()

    elif tag == 'sup':
      self.verify_top(token_sup())
      self.pop()

    elif tag == 'title':
      self.verify_top(token_title())
      self.pop()

    elif tag == 'table':
      self.verify_top(token_table())
      self.pop()

    elif tag == 'td':
      self.verify_top(token_td())
      self.pop()

    elif tag == 'th':
      self.verify_top(token_th())
      self.pop()

    elif tag == 'tr':
      self.verify_top(token_tr())
      self.pop()

    elif tag == 'tbody':
      pass

    elif tag == 'tt':
      self.verify_top(token_tt())
      self.pop()

    elif tag == 'ul':
      self.indent -= 2
      self.verify_top(token_ul())
      self.pop()

    else:
      print ("unhandled end tag: " + tag)


  def handle_data(self, data):
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
  
    if name == 'Aring':
      self.top().tokens.append(token_text('&#8491;'))  # Angstrom Symbol; same as &#197; and &#8491;
    elif name == 'copy':
      self.top().tokens.append(token_text('(c)'))      # Copyright Symbol
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
    elif name == 'ge':
      self.top().tokens.append(token_text('&#8805;'))
    elif name == 'amp':
      self.top().tokens.append(token_text('&'))
    elif name == 'nbsp':
      self.top().tokens.append(token_text(' '))
    elif name == 'ndash':
      self.top().tokens.append(token_text('-'))
    elif name == 'ouml':                               # Umlaut 'ö'; 
      self.top().tokens.append(token_text('o'))        # Only used incorrectly in "Angströms"
    elif name == 'times':
      self.top().tokens.append(token_text('*'))        # same as &#215;
    elif name == 'quot':
      self.top().tokens.append(token_text('"'))
    elif name == 'deg':
      self.top().tokens.append(token_text('&#176;'))   # degree sign
    elif name == 'sum':
      self.top().tokens.append(token_text('&#8721;'))  # sum sign, same as &sum;

    elif name == 'alpha':
      self.top().tokens.append(token_text('\alpha'))   # Greek letter alpha, lower case
    elif name == 'beta':
      self.top().tokens.append(token_text('\beta'))    # Greek letter beta, lower case, same as &#946;
    elif name == 'gamma':
      self.top().tokens.append(token_text('\gamma'))   # Greek letter gamma, lower case, same as &#947;
    elif name == 'chi':
      self.top().tokens.append(token_text('\chi'))     # Greek letter chi, lower case
    elif name == 'delta':
      self.top().tokens.append(token_text('\delta'))   # Greek letter delta, lower case
    elif name == 'lambda':
      self.top().tokens.append(token_text('\lambda'))  # Greek letter lambda, lower case, same as &#955;
    elif name == 'pi':
      self.top().tokens.append(token_text('\pi'))      # Greek letter pi, lower case, same as &#960;
    elif name == 'sigma':
      self.top().tokens.append(token_text('\sigma'))   # Greek letter sigma, lower case, same as &#963;
    elif name == 'theta':
      self.top().tokens.append(token_text('\theta'))   # Greek letter theta, lower case, same as &#952;
    elif name == 'Chi':
      self.top().tokens.append(token_text('\Chi'))     # Greek letter chi, upper case
    elif name == 'Delta':
      self.top().tokens.append(token_text('\Delta'))   # Greek letter delta, upper case, same as &#916;
    elif name == 'Sigma':
      self.top().tokens.append(token_text('\Sigma'))   # Greek letter sigma, upper case
    elif name == 'Theta':
      self.top().tokens.append(token_text('\Theta'))   # Greek letter theta, upper case, same as &#920;

    else:
      print("unhandled entityref: " + name)
      self.top().tokens.append(token_text(chr(name2codepoint[name])))
    
  def handle_charref(self, name):      
    if name == '215':                                  # Same as &times;
      self.top().tokens.append(token_text('*'))
    elif name == '246':                                # Umlaut 'ö'; 
      self.top().tokens.append(token_text('o'))        # Only used incorrectly in "Angströms"
    elif name == '916':
      self.top().tokens.append(token_text('\Delta'))   # Greek letter &Delta;
    elif name == '920':
      self.top().tokens.append(token_text('\Theta'))   # Greek letter &Theta;
    elif name == '946':
      self.top().tokens.append(token_text('\beta'))    # Greek letter &beta;
    elif name == '947':
      self.top().tokens.append(token_text('\gamma'))   # Greek letter &gamma;
    elif name == '948':
      self.top().tokens.append(token_text('\delta'))   # Greek letter &delta;
    elif name == '951':
      self.top().tokens.append(token_text('\eta'))     # Greek letter &eta;
    elif name == '955':
      self.top().tokens.append(token_text('\lambda'))  # Greek letter &lambda;
    elif name == '952':
      self.top().tokens.append(token_text('\\theta'))   # Greek letter &theta;
    elif name == '957':
      self.top().tokens.append(token_text('\nu'))      # Greek letter &nu;
    elif name == '960':
      self.top().tokens.append(token_text('\pi'))      # Greek letter &pi;
    elif name == '961':
      self.top().tokens.append(token_text('\rho'))     # Greek letter &rho;
    elif name == '963':
      self.top().tokens.append(token_text('\sigma'))   # Greek letter &sigma;
    elif name == '964':
      self.top().tokens.append(token_text('\\tau'))     # Greek letter &tau;
    elif name == '8212':
      # em-dash or something?
      self.top().tokens.append(token_text('-'))
    elif name == '197' or name == '8491':
      self.top().tokens.append(token_text('&#8491;'))  # Angstrom Symbol (#197; is also &Aring;)
    elif name == '8721':
      self.top().tokens.append(token_text('&#8721;'))  # Sum Sign (&sum;)
    elif name == '8804':
      self.top().tokens.append(token_text('&#8804;'))  # less than or equal (&le;)
    elif name == '8805':
      self.top().tokens.append(token_text('&#8805;'))  # greater than or equal (&ge;)
    else:
      if name.startswith('x'):
        c = chr(int(name[1:], 16))
      else:
        c = chr(int(name))
      print("unhandled charref: {}: {} ({})".format(HTMLParser.getpos(self), name, c))
      self.top().tokens.append(token_text(c))


  def toMarkdown(self):
    markdown = []
    for token in self.document.tokens:
      markdown.append(token.toMarkdown())
    return '\n'.join(markdown)



arguments = argparse.ArgumentParser(description='Convert HTML manuals to markdown')
arguments.add_argument('html', action = 'store', nargs=1,
             help='a file name to read and convert')
argv = arguments.parse_args()

f = open(argv.html[0])
data = f.read()
f.close()

parser = manualparser()
parser.feed(data)
md = parser.toMarkdown()

if parser.top() != parser.document:
  print('error: stack not empty')
  print(parser.stack)
else:
  print(md)


