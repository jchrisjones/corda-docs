#!/usr/bin/env python3

import logging
import os
import shutil
import sys
import re
import argparse
from pathlib import Path
import json
import toml
import yaml

from sphinx.cmd.build import main as sphinx_main
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
from distutils.dir_util import copy_tree

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(THIS_DIR)
REPOS = os.path.join(ROOT, "repos")
CONTENT = os.path.join(ROOT, "content")
REPOS_ROOT = os.path.join(REPOS, "en/docs") # don't rely on this.

LOG = logging.getLogger(__name__)
ARGS = None

#  Loosely based on https://github.com/sixty-north/rst_to_md/
#  Getting this working inside sphinx and *debugging* is poorly documented
#  (aside from installing as an extension).
#  Easy to convert rst -> xml -> (hugo) markdown

def _setup_logging():
    # LOG.setLevel(logging.WARN)
    LOG.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s:  %(message)s')
    ch.setFormatter(formatter)
    LOG.addHandler(ch)



""" Path-to-source is based on where we checked code in the get_repos.sh script """
def _path_to_github_url(path):
    relpath = str(path.replace(REPOS_ROOT, ""))
    repo = None
    if relpath.startswith("/corda-os/"):
        relpath = relpath.replace("/corda-os/", "release/os/")
        repo = "corda"
    elif relpath.startswith("/corda-enterprise/"):
        repo = "enterprise"
        relpath = relpath.replace("/corda-enterprise/", "release/ent/")
    elif relpath.startswith("/cenm/"):
        repo = "network-services"
        relpath = relpath.replace("/cenm/", "release/")
    else:
        assert False, "No such repo"

    return f"https://github.com/corda/{repo}/blob/{relpath}"


"""  All opening html elements *seem* to require a clear blank line between it and the content
so all opening divs are suffixed with \n\n
"""
class Markdown:
    def __init__(self):
        self.name = 'md'

    def image(self, url, alt):
        return f'![{alt}]({url} "{alt}")'

    def link(self, url, text):
        return f'[{text}]({url})'

    def comment(self, text):
        return f'<-- {text} -->'

    def toc(self):
        return self.comment("page table of contents tags_to_removed")

    def visit_emphasis(self):
        return '*'

    def depart_emphasis(self):
        return '*'

    def visit_strong(self):
        return '**'

    def depart_strong(self):
        return '**'

    def visit_subscript(self):
        return '<sub>'

    def depart_subscript(self):
        return '</sub>'

    def visit_superscript(self):
        return '<sup>'

    def depart_superscript(self):
        return '</sup>'

    def visit_literal(self):
        return '`'

    def depart_literal(self):
        return '`'

    def visit_literal_block(self, lang):
        return f'```{lang}'

    def depart_literal_block(self):
        return '```'

    def visit_math(self):
        return '$'

    def depart_math(self):
        return '$'

    def visit_tab(self, lang):
        return f'<div class="r3-tab">\n\n'

    def depart_tab(self):
        return '\n</div>\n'

    def visit_tabs(self, idx):
        return f'<div class="r3-tabs" id="tabs-{idx}">\n\n'

    def depart_tabs(self):
        return '\n</div>\n'

    def visit_note(self):
        return '<div class="r3-o-note" role="alert"><span>Note: </span>\n\n'

    def depart_note(self):
        return '\n</div>\n'

    def visit_warning(self):
        return '<div class="r3-o-warning" role="alert"><span>Warning: </span>\n\n'

    def depart_warning(self):
        return '\n</div>\n'

    def visit_attention(self):
        return '<div class="r3-o-attention" role="alert"><span>Attention: </span>\n\n'

    def depart_attention(self):
        return '\n</div>\n'

    def visit_important(self):
        return '<div class="r3-o-important" role="alert"><span>Important: </span>\n\n'

    def depart_important(self):
        return '\n</div>\n'

    def visit_topic(self):
        return '<div class="r3-o-topic" role="alert"><span>Topic: </span>\n\n'

    def depart_topic(self):
        return '\n</div>\n'

    def visit_table(self):
        return '\n<div class="table table-sm table-striped table-hover">\n\n'

    def depart_table(self):
        return '\n</div>\n\n'

    def visit_tabs_header(self):
        return "<!-- tabs header end -->"

    def depart_tabs_header(self):
        return "<!-- tabs header end -->"

    def tab_header(self, label, idx):
        return f"<!-- tab header {label} {idx} -->"

"""  Override raw Markdown with Hugo shortcodes  """
class Gatsby(Markdown):
    def __init__(self, *args, **kwargs):
        super(Gatsby, self).__init__(**kwargs)
        self.name = 'gatsby'
        self.tab_index = 0

    def visit_tab(self, lang):
        return '<TabPanel value={value} index={' + str(self.tab_index) + '}>\n\n'

    def depart_tab(self):
        self.tab_index += 1
        return '\n</TabPanel>\n'

    def visit_tabs(self, idx):
        return f'<div>'

    def depart_tabs(self):
        self.tab_index = 0
        return '\n</div>\n'

    def visit_tabs_header(self):
        return '<Tabs value={value} aria-label="code tabs">'

    def depart_tabs_header(self):
        return "</Tabs>"

    def tab_header(self, label, idx):
        return f'<Tab label="{label}" />'


"""  Override raw Markdown with Hugo shortcodes  """
class Hugo(Markdown):
    def __init__(self, *args, **kwargs):
        super(Hugo, self).__init__(**kwargs)
        self.name = 'hugo'

    # def image(self, url, alt):
    #     f'{{{{< img src="{url}" alt="{alt}" >}}}}\n\n'

    def visit_tabs(self, idx):
        return f'\n{{{{< tabs name="tabs-{idx}" >}}}}\n'

    def depart_tabs(self):
        return "{{< /tabs >}}\n\n"

    def visit_tab(self, lang):
        return f'\n{{{{% tab name="{lang}" %}}}}\n'

    def depart_tab(self):
        return f'{{{{% /tab %}}}}\n'

    def comment(self, s):
        return f"\n{{{{/* {s} */}}}}\n"

    def visit_note(self):
        return "\n{{< note >}}"

    def depart_note(self):
        return "{{< /note >}}\n"

    def visit_warning(self):
        return "\n{{< warning >}}"

    def depart_warning(self):
        return "{{< /warning >}}\n\n"

    def visit_attention(self):
        return "\n{{< attention >}}\n"

    def depart_attention(self):
        return "\n{{< /attention >}}\n"

    def visit_important(self):
        return "\n{{< important >}}"

    def depart_important(self):
        return "\n{{< /important >}}\n"

    def visit_topic(self):
        return "\n{{< topic >}}"

    def depart_topic(self):
        return "\n{{< /topic >}}"

    def visit_table(self):
        return "\n{{< table >}}\n"

    def depart_table(self):
        return "\n{{< /table >}}\n"

    def visit_tabs_header(self):
        return None

    def depart_tabs_header(self):
        return None

    def tab_header(self, label, idx):
        return None


class Context:
    def __init__(self):
        self.head = []
        self.body = []
        self.foot = []

    # You probably don't want this
    def put_head(self, text):
        self.head.append(text)

    def put_body(self, text):
        self.body.append(text)

    # You probably don't want this
    def put_foot(self, text):
        self.foot.append(text)

    def finalize(self):
        pass

    def __add__(self, other):
        self.head += other.head
        self.body += other.body
        self.foot += other.foot
        return self

    def astext(self):
        return ''.join(self.head + self.body + self.foot)


class TableContext(Context):
    def __init__(self, *args, **kwargs):
        super(TableContext, self).__init__(**kwargs)
        self.cols = []
        self.col_titles = []
        self.current_col = 0

    # def finalize(self):
    #     self.body = markdown_table


def _is_xml_padding(s):
    likely_xml_padding = s and s.startswith('\n') and s.strip() == ''
    return likely_xml_padding or not s


class Translator:
    def __init__(self, cms):
        self._context = [Context()]
        self.cms = cms

        # For determining h1/h2/h3 etc.
        self.section_depth = 0
        self.tabs_counter = 0

        # We shouldn't have nested containers so this should be enough for tabbed code panes.
        self.in_tabs = False

        self._elements = [None]
        self._ordered_list = [0]

        self.front_matter = {}
        self.front_matter["date"] = "2020-01-08T09:59:25Z"

    """Returns the final document"""

    def astext(self):
        """Return the final formatted document as a string."""
        return self.top.astext()

    @property
    def top(self):
        return self._context[-1]

    def push_context(self, ctx):
        self._context.append(ctx)

    def pop_context(self):
        head = self._context[-1]
        head.finalize()
        self._context = self._context[:-1]
        self._context[-1] += head

    def push_element(self, e):
        self._elements.append(e)

    def pop_element(self):
        self._elements = self._elements[:-1]

    def _walk(self, parent):
        for e in parent:
            self.push_element(e.tag)
            visit_func = getattr(self, f'visit_{e.tag}', visit_unsupported)
            depart_func = getattr(self, f'depart_{e.tag}', visit_unsupported)

            self.push_context(Context())
            visit_func(e)
            likely_xml_padding = e.text and e.text.startswith('\n') and e.text.strip() == ''

            #  <tag>TAG_BODY<other>OTHER_BODY<other>OTHER_TAIL</tag>TAG_TAIL
            table_tags = ['entry', 'thead', 'tgroup', 'colspec', 'row', 'tbody']
            if likely_xml_padding:
                if e.tag not in table_tags:
                    self.top.put_body('\n')
                else:
                    pass  # chomp
            elif e.text:
                self.top.put_body(e.text)

            self._walk(e)
            depart_func(e)

            #  Half of this is XML formatting between elements

            inline_tags = ['literal', 'emphasis', 'strong', 'subscript', 'superscript',
                           'reference', 'inline' 'target']
            #
            # if e.tag in inline_tags and e.tail:  # and e.tail.strip() != '':
            #     self.top.put_body(e.tail)

            likely_xml_padding = e.tail and e.tail.startswith('\n    ') and e.tail.strip() == ''

            if likely_xml_padding and e.tag not in inline_tags:
                pass
            elif e.tail:
                self.top.put_body(e.tail)

            self.pop_context()
            self.pop_element()

    def walk(self, filename):
        tree = ET.parse(filename)
        self.filename = filename
        self._walk([tree.getroot()])
        self._add_front_matter()

    def _fix_up_javadoc(self, link):
        LOG.debug("TODO: fix up javadoc")
        return '#'

    """ Add in some front-matter tags derived from the file """
    def _add_front_matter(self):
        dirs = str(self.filename).split("/")

        while dirs[0] != "docs":
            dirs.pop(0)

        # "version" that this page is in/under, e.g. corda-os-4-3
        # we CANNOT have '.' in a 'toml' config section name - that implies hierarchy
        project_name = dirs[1]
        semantic_version = dirs[2]
        version = (project_name + "-" + semantic_version).replace(".", "-")

        filename_only = os.path.basename(os.path.splitext(self.filename)[0])
        #  convienience
        dest_file = str(self.filename).replace('docs/xml/xml/', '').replace(".xml", ".md")

        dirname_only = os.path.basename(os.path.dirname(dest_file))
        project_only = os.path.basename(os.path.dirname(os.path.dirname(dest_file)))

        # Are we parsing the index file under <project>/MAJOR.MINOR?
        is_version_index = filename_only == "index" and re.findall(r"\d\.\d", dirname_only)

        # Yes?  Rewrite the front matter titles to something consistent
        if is_version_index:
            if project_only == "corda-os":
                self.front_matter["title"] = "Corda OS " + dirname_only
            elif project_only == "corda-ent":
                self.front_matter["title"] = "Corda Enterprise " + dirname_only
            elif project_only == "cenm":
                self.front_matter["title"] = "CENM " + dirname_only

        # Menu entries that this page should occur in:
        menu = self.front_matter.get("menu", {})

        # Specifically figure out what this menu should be.
        # Add each menu as a dict
        menu_entry = {}
        if filename_only.startswith("api-"):
            menu_entry = { "parent": version + "-api" }
        elif filename_only.startswith("key-concepts-"):
            menu_entry = { "parent": version + "-concepts" }
        elif filename_only.startswith("node-"):
            menu_entry = { "parent": version + "-node" }
        elif filename_only.startswith("tutorial-"):
            menu_entry = { "parent": version + "-tutorial" }
        elif filename_only.startswith("config-"):
            menu_entry = { "parent": version + "-config" }

        # e.g. if 4.4/index
        if is_version_index:
            LOG.warning(f"Adding {self.filename} to 'versions' menu")
            versions_menu_entry = {}
            LOG.warning(f"Adding parameter 'section_menu={version}' for this index page only'")
            self.front_matter["section_menu"] = version
            self.front_matter["version"] = semantic_version
            self.front_matter["project"] = project_name
            # Ordering in the versions menu
            if project_name == "cenm":
                versions_menu_entry["weight"] = (100 - int(float(semantic_version)*10)) + 1000
            elif project_name == "corda-os":
                versions_menu_entry["weight"] = (100 - int(float(semantic_version)*10)) + 500
            if project_name == "corda-enterprise":
                versions_menu_entry["weight"] = (100 - int(float(semantic_version)*10)) + 100
            menu["versions"] = versions_menu_entry

        # Set the menu entry for { "corda-os-4-3": { ... } }
        menu[version] = menu_entry

        # All the values are empty dict, so we can safely use a list
        # of menus we're in instead.
        if all(not bool(v) for __, v in menu.items()):
            menu = [k for k, __ in menu.items()]

        # Add menu entry(-ies) to front matter
        self.front_matter["menu"] = menu

        # Finally, handle missing page titles, if any
        # use the filename (no extension) if the title is missing.
        if "title" not in self.front_matter:
            self.front_matter["title"] = filename_only

        self._front_matter_add_tags_and_categories(filename_only)

    """  Add some tags based on the filename into the front matter
    and add some reasonable categories too """
    def _front_matter_add_tags_and_categories(self, filename_only):
        tags_to_remove = ['index', '_index', 'and', 'a', 'the', 'if', 'key', 'hello', 'world', 'toc', 'toctree', 'one', 'two', 'three', 'up', 'with', 'dir' 'docs', 'eta', 'non', 'reg', 'reqs', 'run', 'runs', 'sub', 'soft', 'tree', 'to', 'up', 'writing']

        tags = filename_only.split("-")
        for r in tags_to_remove:
            if r in tags: tags.remove(r)

        if tags:
            self.front_matter['tags'] = tags


    ###########################################################################
    # Visitors
    ###########################################################################

    #  Some we use, but sphinx renders into the simplified output (such as
    #  plain old 'emphasis'
    #
    # https://docutils.sourceforge.io/docs/user/rst/quickref.html#definition-lists
    #
    # https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet#links

    def visit_title_reference(self, node):
        self.top.put_body(self.cms.visit_emphasis())

    def depart_title_reference(self, node):
        self.top.put_body(self.cms.depart_emphasis())

    def visit_section(self, node):
        self.section_depth += 1

    def depart_section(self, node):
        self.section_depth -= 1

    def visit_title(self, node):
        h = self.section_depth * '#'
        self.top.put_body(h + ' ')

    def depart_title(self, node):
        if self.section_depth == 1 and 'title' not in self.front_matter:
            self.front_matter['title'] = node.text

        self.top.put_body('\n\n')

    def visit_block_quote(self, node):
        class QuoteContext(Context):
            def finalize(self):
                quoted = ['> {}'.format(line) for line in self.body[:1]] + self.body[1:]
                quoted = [line.replace('\n', '\n> ') for line in quoted[:-1]] + quoted[-1:]
                self.body = quoted

        self.push_context(QuoteContext())

    def depart_block_quote(self, node):
        self.pop_context()

    def visit_raw(self, node):
        self.push_context(Context())

    def depart_raw(self, node):
        # Chomp....
        out = []
        for line in self.top.body:
            if not any([s in line for s in ['codesets.js', 'jquery.js']]):
                out.append(line)
        self.top.body = out
        self.pop_context()

    def visit_definition(self, node):
        pass

    def depart_definition(self, node):
        pass

    def visit_reference(self, node):
        self.push_context(Context())

    def depart_reference(self, node):
        text = "".join(self.top.body)
        self.top.body = []
        self.pop_context()

        link = '#'
        if 'refuri' in node.attrib:
            uri = node.attrib['refuri']
            link = uri
            # Could be a local path or another page
            if not link.startswith('http'):
                non_fragment = link.split('#')[0]
                __, ext = os.path.splitext(non_fragment)
                # If it doesn't have a suffix, it's another page
                if not ext:
                    if '#' in link:
                        link = link.replace('#', '.md#')
                    else:
                        link = link + '.md'

            else:
                LOG.debug(f"Regular link: {link}")
                if 'javadoc' in link:
                    link = self._fix_up_javadoc(link)
                pass
        elif 'refid' in node.attrib:
            # Anchor link to the same page
            link = '#' + node.attrib['refid']

        self.top.put_body(self.cms.link(link, text))

    def visit_definition_list_item(self, node):
        # we don't really do anything with this?
        pass

    def depart_definition_list_item(self, node):
        pass

    def visit_strong(self, node):
        self.top.put_body(self.cms.visit_strong())

    def depart_strong(self, node):
        self.top.put_body(self.cms.depart_strong())

    def visit_bullet_list(self, node):
        pass

    def depart_bullet_list(self, node):
        pass

    def visit_topic(self, node):
        if node.attrib.get('names', '') == 'contents':
            # replace table of contents with hugo version
            if ARGS.toc:
                self.top.put_body(self.cms.toc())
            self.push_context(Context())
        else:
            self.top.put_body(self.cms.visit_topic())

    def depart_topic(self, node):
        if node.attrib.get('names', '') == 'contents':
            self.top.body = []  # chomp the old table of contents
            self.pop_context()
        else:
            self.top.put_body(self.cms.depart_topic())

    def visit_emphasis(self, node):
        self.top.put_body(self.cms.visit_emphasis())

    def depart_emphasis(self, node):
        self.top.put_body(self.cms.depart_emphasis())

    def visit_literal_block(self, node):
        lang = node.attrib.get('language', '')
        if self.in_tabs:
            self.top.put_head(lang)
            self.top.put_body(self.cms.visit_tab(lang))
        self.top.put_body(self.cms.visit_literal_block(lang) + '\n')

    def depart_literal_block(self, node):
        self.top.put_body('\n' + self.cms.depart_literal_block() + '\n')
        if self.in_tabs:
            self.top.put_body(self.cms.depart_tab())

        if node.attrib.get('source', None):
            src = node.attrib['source']

            if self.in_tabs:
                #  append each one in the footer so it appears beneath the 'tabs' collection, rather
                #  than under the tab
                self.top.put_foot(self.cms.link(_path_to_github_url(src), os.path.basename(src)))
            else:
                # not in a collection, put it straight under the 'tab' (which) doesn't exist
                self.top.put_body(self.cms.link(_path_to_github_url(src), os.path.basename(src)))

    def visit_inline(self, node):
        pass

    def depart_inline(self, node):
        pass

    def visit_container(self, node):
        self.in_tabs = True
        self.tabs_counter += 1
        self.top.put_body(self.cms.visit_tabs(self.tabs_counter))
        # We are putting the links to the source in each tab in the footer.
        # Similarly we store the tab title in the header (even if we don't use it)
        self.push_context(Context())

    def depart_container(self, node):
        # Gather up any source code links, and add them to the end.
        if (self.top.foot):
            self.top.foot.append(self.cms.image("/images/svg/github.svg", "github"))
            md = "\n" + " | ".join(self.top.foot) + "\n\n"
        else:
            md = None

        tabs_header = []
        tabs_header.append(self.cms.visit_tabs_header())
        idx = 0
        for item in self.top.head:
            tabs_header.append(self.cms.tab_header(item, idx))
            idx += 1
        tabs_header.append(self.cms.depart_tabs_header())
        tabs_header = [x for x in tabs_header if x is not None]
        self.top.body = tabs_header + self.top.body

        self.top.foot = []
        self.top.head = []
        self.pop_context() # tab content was written to top which we're now popping.
        if md:
            self.top.body.append(md)

        self.top.put_body(self.cms.depart_tabs())
        self.in_tabs = False

    def visit_definition_list(self, node):
        # We don't really seem to care about this - it will be emitted as a bullet list
        pass

    def depart_definition_list(self, node):
        pass

    def visit_target(self, node):
        pass

    def depart_target(self, node):
        #  Don't think we need this - we end up with a double link
        #  Typically handled by 'reference'
        # text = node.attrib.get('names', "FIXME")
        # link = node.attrib.get('refuri', "#")
        # self.top.put_body(f"[{text}]({link})")
        pass

    def visit_paragraph(self, node):
        pass

    def depart_paragraph(self, node):
        if self._elements[-2] == "entry":
            return  # in a table

        self.top.put_body('\n\n')

    def visit_image(self, node):
        # Not using markdown, as some of the images are massive
        # and need rescaling.

        # TODO:  wrap image in <div aria-label="..."> ?
        # and make that a shortcode?
        if 'uri' not in node.attrib:
            url = '#'
            alt = 'missing'
        else:
            url = node.attrib.get('uri', '#')
            alt = os.path.splitext(os.path.basename(url))[0].replace('-', ' ').replace('_', ' ')

        self.top.put_body(self.cms.image(url, os.path.basename(alt)))

    def depart_image(self, node):
        pass

    def visit_enumerated_list(self, node):
        pass

    def depart_enumerated_list(self, node):
        pass

    def visit_document(self, node):
        pass

    def depart_document(self, node):
        pass

    def visit_warning(self, node):
        self.top.put_body(self.cms.visit_warning())

    def depart_warning(self, node):
        self.top.put_body(self.cms.depart_warning())

    def visit_literal(self, node):
        self.top.put_body(self.cms.visit_literal())

    def depart_literal(self, node):
        self.top.put_body(self.cms.visit_literal())

    def visit_note(self, node):
        self.top.put_body(self.cms.visit_note())

    def depart_note(self, node):
        self.top.put_body(self.cms.depart_note())

    def visit_list_item(self, node):
        self.push_context(Context())
        bullet_depth = sum([1 for e in self._elements if e == 'bullet_list']) - 1
        padding = '    ' * bullet_depth
        self.top.put_body(padding + '* ')

    def depart_list_item(self, node):
        if '\n' in self.top.body[1]:
            self.top.body[1] = self.top.body[1].replace('\n', '')
        self.top.put_body('\n')
        self.pop_context()

    def visit_term(self, node):
        LOG.debug('Not implemented term')

    def depart_term(self, node):
        LOG.debug('Not implemented term')

    def visit_comment(self, node):
        self.push_context(Context())

    def depart_comment(self, node):
        # chomp comments
        self.top.body = []
        self.pop_context()

    def visit_attention(self, node):
        self.top.put_body(self.cms.visit_attention())

    def depart_attention(self, node):
        self.top.put_body(self.cms.depart_attention())

    def visit_compact_paragraph(self, node):
        pass

    def depart_compact_paragraph(self, node):
        self.top.put_body('\n')

    def visit_compound(self, node):
        LOG.debug('Not implemented compound')

    def depart_compound(self, node):
        LOG.debug('Not implemented compound')

    def visit_field_list(self, node):
        LOG.debug('Not implemented field_list')

    def depart_field_list(self, node):
        LOG.debug('Not implemented field_list')

    def visit_field(self, node):
        LOG.debug('Not implemented field')

    def depart_field(self, node):
        LOG.debug('Not implemented field')

    def visit_field_body(self, node):
        LOG.debug('Not implemented field_body')

    def depart_field_body(self, node):
        LOG.debug('Not implemented field_body')

    def visit_field_name(self, node):
        LOG.debug('Not implemented field_name')

    def depart_field_name(self, node):
        LOG.debug('Not implemented field_name')

    def visit_important(self, node):
        self.top.put_body(self.cms.visit_important())

    def depart_important(self, node):
        self.top.put_body(self.cms.depart_important())

    def visit_problematic(self, node):
        LOG.debug('Not implemented problematic')

    def depart_problematic(self, node):
        LOG.debug('Not implemented problematic')

    def visit_line_block(self, node):
        LOG.debug('Not implemented line_block')

    def depart_line_block(self, node):
        LOG.debug('Not implemented line_block')

    def visit_line(self, node):
        LOG.debug('Not implemented line')

    def depart_line(self, node):
        LOG.debug('Not implemented line')

    def visit_table(self, node):
        self.top.put_body(self.cms.visit_table())
        self.push_context(TableContext())

    def depart_table(self, node):
        self.top.put_body(self.cms.depart_table())
        self.pop_context()

    def visit_colspec(self, node):
        table_context = next((ctx for ctx in (reversed(self._context)) if isinstance(ctx, TableContext)), None)
        if not table_context:
            raise RuntimeError("Expected a TableContext on the stack")
        col_width = int(node.attrib.get('colwidth'), 0)
        assert col_width != 0, "No col width?"

        table_context.cols.append(col_width)

    def depart_colspec(self, node):
        pass

    def visit_tgroup(self, node):
        pass  # might need to do something here

    def depart_tgroup(self, node):
        pass

    def visit_row(self, node):
        table_context = next((ctx for ctx in (reversed(self._context)) if isinstance(ctx, TableContext)), None)
        table_context.current_col = 0
        self.top.put_body('|')

    def depart_row(self, node):
        self.top.put_body('\n')

    def visit_thead(self, node):
        pass

    def depart_thead(self, node):
        table_context = next((ctx for ctx in (reversed(self._context)) if isinstance(ctx, TableContext)), None)
        self.top.put_body('|')
        for col_width in table_context.cols:
            delim = col_width * '-'
            delim += '|'
            self.top.put_body(delim)
        self.top.put_body('\n')

    def visit_tbody(self, node):
        LOG.debug('Not implemented tbody')

    def depart_tbody(self, node):
        LOG.debug('Not implemented tbody')

    def visit_entry(self, node):
        table_context = next((ctx for ctx in (reversed(self._context)) if isinstance(ctx, TableContext)), None)
        table_context.current_col += 1

    def depart_entry(self, node):
        self.top.put_body('|')

    def visit_caption(self, node):
        pass

    def depart_caption(self, node):
        self.top.put_body('\n')

    def visit_label(self, node):
        self.top.put_body("\[")

    def depart_label(self, node):
        self.top.put_body("\] ")

    def visit_footnote(self, node):
        d = node.attrib['docname']
        b = node.attrib['backrefs']
        link = f'\n\n<a name="{d}-{b}"></a>\n'
        self.top.put_body(link)
        pass

    def depart_footnote(self, node):
        pass

    def visit_footnote_reference(self, node):
        self.top.put_body("<sup>[\[")

    def depart_footnote_reference(self, node):
        d = node.attrib['docname']
        b = node.attrib['ids']
        link = f'#{d}-{b}'
        self.top.put_body(f"\]]({link})")

    def visit_transition(self, node):
        LOG.debug('Not implemented transition')

    def depart_transition(self, node):
        LOG.debug('Not implemented transition')

    def visit_classifier(self, node):
        LOG.debug('Not implemented classifier')

    def depart_classifier(self, node):
        LOG.debug('Not implemented classifier')

    def visit_figure(self, node):
        LOG.debug('Not implemented figure')

    def depart_figure(self, node):
        LOG.debug('Not implemented figure')

    #  RAW HTML ELEMENTS?
    def _raw_html(self, node):
        attribs = []
        for key in node.attrib:
            attribs.append(f' {key}="{node.attrib[key]}"')
        v = "".join(attribs)
        value = f"<{node.tag}{v}>"
        self.top.put_body(value)

    def visit_script(self, node):
        pass  # no scripts, we're not using the old sphinx stuff any more

    def depart_script(self, node):
        pass  # no scripts, thanks

    def visit_style(self, node):
        pass  # don't think we need the style sheets from sphinx either

    def depart_style(self, node):
        pass

    def visit_iframe(self, node):
        self._raw_html(node)

    def depart_iframe(self, node):
        self.top.put_body(f"</{node.tag}>\n\n")

    def visit_p(self, node):
        self._raw_html(node)

    def depart_p(self, node):
        self.top.put_body(f"</{node.tag}>\n")

    def visit_embed(self, node):
        self._raw_html(node)

    def depart_embed(self, node):
        self.top.put_body(f"</{node.tag}>\n\n")

    def visit_a(self, node):
        self._raw_html(node)

    def depart_a(self, node):
        self.top.put_body(f"</{node.tag}>")

    def visit_button(self, node):
        self._raw_html(node)

    def depart_button(self, node):
        self.top.put_body(f"</{node.tag}>")

    def visit_toctree(self, node):
            LOG.debug('Not implemented toctree')

    def depart_toctree(self, node):
            LOG.debug('Not implemented toctree')


############################################################################
#  END OF CLASS

# NOT A CLASS MEMBER
def visit_unsupported(self, node):
    print(f"Unsupported {node.tag}")


def configure_translator(filename):
    s = set()

    tree = ET.parse(filename)
    for e in tree.iter():
        s.add(e.tag)

    failed = False
    for tag in s:
        if hasattr(Translator, f'visit_{tag}'):
            continue

        # Not supported.
        setattr(Translator, f'visit_{tag}', visit_unsupported)

        #  Output what the user needs to implement to support it
        print("PASTE THIS IN TO THE PYTHON\n\n\n")
        print(f"\tdef visit_{tag}(self, node):\n\t\tLOG.debug('Not implemented {tag}')")
        print("")
        print(f"\tdef depart_{tag}(self, node):\n\t\tLOG.debug('Not implemented {tag}')")

        failed = True

    if failed:
        LOG.error(f"Add missing directives to continue.  Found when processing {filename}")
        sys.exit(1)


def write_frontmatter(f, front_matter):
    if ARGS.yaml:
        f.write('---\n'),
        f.write(yaml.dump(front_matter))
        f.write('---\n')
    else:
        f.write('+++\n')
        f.write(toml.dumps(front_matter))
        f.write('+++\n')


def convert_one_xml_file_to_cms_style_md(cms, filename):
    LOG.debug(f"Processing {filename}")

    try:
        configure_translator(filename)
        t = Translator(cms)
        t.walk(filename)

        md = str(filename).replace('.xml', '.md')
        with open(md, 'w') as f:
            write_frontmatter(f, t.front_matter)
            f.write(t.astext())
    except ParseError as e:
        line, col = e.position
        LOG.error(f"When processing: {filename}:{line}")
        raise


def convert_all_xml_to_md(cms):
    LOG.warning("Converting all xml => md")

    files = [x for x in Path(REPOS).rglob('xml/xml/**/*.xml')]
    for x in files:
        convert_one_xml_file_to_cms_style_md(cms, x)

    LOG.warning(f"Processed {len(files)} files")


def run_sphinx(src_dir):
    src = os.path.abspath(src_dir)
    dest = os.path.join(os.path.dirname(src), 'xml')

    #  Always rebuild (-a)
    #  Set xmlmode tag to pull out the rest of the HTML output
    args = ["-M", "xml", src, dest, "-a", "-t", "xmlmode"]
    retval = sphinx_main(args)
    if retval != 0:
        sys.exit(retval)

    return dest


def _search_and_replace(files, replacements):
    for file in files:
        LOG.debug(f"Checking {file}")
        lines = open(file, 'r').readlines()
        updated = False
        count = 0
        for line in lines:
            for (value, new_value) in replacements:
                if value in line:
                    line = line.replace(value, new_value)
                    lines[count] = line
                    updated = True
                    LOG.debug(f"Replaced! {value} with {new_value}")
            count += 1
        if updated:
            LOG.info(f"Rewritten file {file}")
            open(file, 'w').writelines(lines)


def preprocess(d):
    LOG.debug(f"Pre-processing {d}")
    replacements = [('.. raw:: html', '.. raw:: xml'), ('.. only:: html', '.. only:: xml')]
    files = [x for x in Path(d).rglob('*.rst')]
    _search_and_replace(files, replacements)


def postprocess(d):
    LOG.debug(f"Post-processing {d}")
    # Also matches: webkitallowfullscreen and mozallowfullscreen
    replacements = [
        ('allowfullscreen', 'allowfullscreen="true"'),
        ('&nbsp;', ' '),
        ('<br>', '')
    ]
    files = [x for x in Path(d).rglob('*.xml')]
    _search_and_replace(files, replacements)


def convert_rst_to_xml():
    LOG.warning("Converting all rst => xml using sphinx")
    dirs = [x for x in Path(REPOS).rglob('docs/source')]
    for d in dirs:
        LOG.warning(f"Converting {d}")
        preprocess(d)
        run_sphinx(d)

    _postprocess_xml()


def _postprocess_xml():
    for d in [x for x in Path(REPOS).rglob('xml/xml')]:
        postprocess(d)


def copy_to_content(cms):
    LOG.warning("Copying all md to content/")

    dirs = []
    files = [x for x in Path(REPOS).rglob('xml/xml/**/*.md')]
    for src in files:
        dest = str(src).replace('docs/xml/xml/', '').replace(REPOS, CONTENT)
        src_filename = os.path.basename(src)
        dirname_only = os.path.basename(os.path.dirname(dest))

        # We need to rename index pages to _index.md (page bundle = section)
        # for hugo when we're in MAJOR.MINOR folders
        # otherwise, we're a plain-old "leaf bundle"
        if ARGS.cms == "hugo" and re.findall(r"\d\.\d", dirname_only):

            index_md = os.path.join(os.path.dirname(dest), '_index.md')

            if src_filename == 'index.md':
                LOG.warning(f"Copying {src} to {dest}")
                dest = index_md  # it was 'index.rst', copying to '_index.md'

        if not os.path.exists(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest), exist_ok=True)

        if dest.endswith("_index.md"):
            LOG.warning(f"Copying {src} {dest}")

        LOG.debug(f"Copying {src} {dest}")
        shutil.copyfile(src, dest)
        if os.path.dirname(dest) not in dirs:
            dirs.append(os.path.dirname(dest))

    LOG.warning(f"Copied {len(files)} files")


def copy_resources_to_content():
    LOG.warning("Copying all resources to content/")

    for d in ['_static', 'resources']:
        dirs = [x for x in Path(REPOS).rglob(f'docs/source/{d}')]
        for src in dirs:
            dest = str(src).replace(f'docs/source/{d}', d).replace(REPOS, CONTENT)
            LOG.debug(f"Copying {src} {dest}")
            copy_tree(src, dest)

    LOG.warning(f"Copied resources")


def create_missing_pages():
    if ARGS.cms not in ["hugo", "markdown"]:
        LOG.warning("Don't know what to do for other CMSs")
        return

    parent_dir = os.path.join(CONTENT, "en", "docs")

    for dir in os.listdir(parent_dir):
        item = os.path.join(parent_dir, dir)
        if not os.path.isdir(item):
            continue
        index_md = os.path.join(item, "_index.md")
        if not os.path.exists(index_md):
            LOG.warning(f"Writing empty: {index_md}")
            open(index_md, 'w').close()


def main():
    global ARGS
    desc = "Convert rst files to md using sphinx"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--yaml", "-y", help="write front matter as yaml, default is toml", default=False, action='store_true')
    parser.add_argument("--toc", "-t", help="include table of contents in the page", default=False, action='store_true')
    parser.add_argument("--skip", "-s", help="skip rst conversion for speed if already done", default=False, action='store_true')
    parser.add_argument("--cms", "-c", help="generate (commonmark) markdown for cms", default='hugo', choices=['gatsby', 'markdown', 'hugo'])
    ARGS = parser.parse_args()

    _setup_logging()

    LOG.warning(f"You need to clone the repositories you wish to convert to {REPOS}")
    LOG.warning(f"You also need to then git checkout the branch you want.")
    LOG.warning(f"There is a script that does this - get_repos.sh")

    if not ARGS.skip:
        convert_rst_to_xml()
    else:
        LOG.warning("Skipping rst-to-xml")

    if ARGS.cms == 'markdown':
        cms = Markdown()  #  Generates hugo-shortcode free markdown - uses divs instead
    elif ARGS.cms == "gatsby":
        cms = Gatsby()  # which simply adds react tags <Tab> <Tabs> etc.
    else:
        cms = Hugo()

    convert_all_xml_to_md(cms)

    # filename = "/home/barry/dev/r3/sphinx2hugo/repos/en/docs/corda-os/4.4/docs/xml/xml/api-contract-constraints.xml"
    # convert_one_xml_file_to_cms_style_md(filename)

    copy_to_content(cms)
    copy_resources_to_content()
    create_missing_pages()


if __name__ == '__main__':
    main()
