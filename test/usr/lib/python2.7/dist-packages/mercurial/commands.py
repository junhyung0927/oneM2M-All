# commands.py - command processing for mercurial
#
# Copyright 2005-2007 Matt Mackall <mpm@selenic.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

import difflib
import errno
import operator
import os
import random
import re
import shlex
import socket
import sys
import tempfile
import time

from .i18n import _
from .node import (
    bin,
    hex,
    nullhex,
    nullid,
    nullrev,
    short,
)
from . import (
    archival,
    bookmarks,
    bundle2,
    changegroup,
    cmdutil,
    commandserver,
    context,
    copies,
    dagparser,
    dagutil,
    destutil,
    discovery,
    encoding,
    error,
    exchange,
    extensions,
    fileset,
    formatter,
    graphmod,
    hbisect,
    help,
    hg,
    hgweb,
    localrepo,
    lock as lockmod,
    merge as mergemod,
    minirst,
    obsolete,
    patch,
    phases,
    policy,
    pvec,
    repair,
    revlog,
    revset,
    scmutil,
    setdiscovery,
    simplemerge,
    sshserver,
    sslutil,
    streamclone,
    templatekw,
    templater,
    treediscovery,
    ui as uimod,
    util,
)

release = lockmod.release

table = {}

command = cmdutil.command(table)

# label constants
# until 3.5, bookmarks.current was the advertised name, not
# bookmarks.active, so we must use both to avoid breaking old
# custom styles
activebookmarklabel = 'bookmarks.active bookmarks.current'

# common command options

globalopts = [
    ('R', 'repository', '',
     _('repository root directory or name of overlay bundle file'),
     _('REPO')),
    ('', 'cwd', '',
     _('change working directory'), _('DIR')),
    ('y', 'noninteractive', None,
     _('do not prompt, automatically pick the first choice for all prompts')),
    ('q', 'quiet', None, _('suppress output')),
    ('v', 'verbose', None, _('enable additional output')),
    ('', 'config', [],
     _('set/override config option (use \'section.name=value\')'),
     _('CONFIG')),
    ('', 'debug', None, _('enable debugging output')),
    ('', 'debugger', None, _('start debugger')),
    ('', 'encoding', encoding.encoding, _('set the charset encoding'),
     _('ENCODE')),
    ('', 'encodingmode', encoding.encodingmode,
     _('set the charset encoding mode'), _('MODE')),
    ('', 'traceback', None, _('always print a traceback on exception')),
    ('', 'time', None, _('time how long the command takes')),
    ('', 'profile', None, _('print command execution profile')),
    ('', 'version', None, _('output version information and exit')),
    ('h', 'help', None, _('display help and exit')),
    ('', 'hidden', False, _('consider hidden changesets')),
]

dryrunopts = [('n', 'dry-run', None,
               _('do not perform actions, just print output'))]

remoteopts = [
    ('e', 'ssh', '',
     _('specify ssh command to use'), _('CMD')),
    ('', 'remotecmd', '',
     _('specify hg command to run on the remote side'), _('CMD')),
    ('', 'insecure', None,
     _('do not verify server certificate (ignoring web.cacerts config)')),
]

walkopts = [
    ('I', 'include', [],
     _('include names matching the given patterns'), _('PATTERN')),
    ('X', 'exclude', [],
     _('exclude names matching the given patterns'), _('PATTERN')),
]

commitopts = [
    ('m', 'message', '',
     _('use text as commit message'), _('TEXT')),
    ('l', 'logfile', '',
     _('read commit message from file'), _('FILE')),
]

commitopts2 = [
    ('d', 'date', '',
     _('record the specified date as commit date'), _('DATE')),
    ('u', 'user', '',
     _('record the specified user as committer'), _('USER')),
]

# hidden for now
formatteropts = [
    ('T', 'template', '',
     _('display with template (EXPERIMENTAL)'), _('TEMPLATE')),
]

templateopts = [
    ('', 'style', '',
     _('display using template map file (DEPRECATED)'), _('STYLE')),
    ('T', 'template', '',
     _('display with template'), _('TEMPLATE')),
]

logopts = [
    ('p', 'patch', None, _('show patch')),
    ('g', 'git', None, _('use git extended diff format')),
    ('l', 'limit', '',
     _('limit number of changes displayed'), _('NUM')),
    ('M', 'no-merges', None, _('do not show merges')),
    ('', 'stat', None, _('output diffstat-style summary of changes')),
    ('G', 'graph', None, _("show the revision DAG")),
] + templateopts

diffopts = [
    ('a', 'text', None, _('treat all files as text')),
    ('g', 'git', None, _('use git extended diff format')),
    ('', 'nodates', None, _('omit dates from diff headers'))
]

diffwsopts = [
    ('w', 'ignore-all-space', None,
     _('ignore white space when comparing lines')),
    ('b', 'ignore-space-change', None,
     _('ignore changes in the amount of white space')),
    ('B', 'ignore-blank-lines', None,
     _('ignore changes whose lines are all blank')),
    ]

diffopts2 = [
    ('', 'noprefix', None, _('omit a/ and b/ prefixes from filenames')),
    ('p', 'show-function', None, _('show which function each change is in')),
    ('', 'reverse', None, _('produce a diff that undoes the changes')),
    ] + diffwsopts + [
    ('U', 'unified', '',
     _('number of lines of context to show'), _('NUM')),
    ('', 'stat', None, _('output diffstat-style summary of changes')),
    ('', 'root', '', _('produce diffs relative to subdirectory'), _('DIR')),
]

mergetoolopts = [
    ('t', 'tool', '', _('specify merge tool')),
]

similarityopts = [
    ('s', 'similarity', '',
     _('guess renamed files by similarity (0<=s<=100)'), _('SIMILARITY'))
]

subrepoopts = [
    ('S', 'subrepos', None,
     _('recurse into subrepositories'))
]

debugrevlogopts = [
    ('c', 'changelog', False, _('open changelog')),
    ('m', 'manifest', False, _('open manifest')),
    ('', 'dir', '', _('open directory manifest')),
]

# Commands start here, listed alphabetically

@command('^add',
    walkopts + subrepoopts + dryrunopts,
    _('[OPTION]... [FILE]...'),
    inferrepo=True)
def add(ui, repo, *pats, **opts):
    """add the specified files on the next commit

    Schedule files to be version controlled and added to the
    repository.

    The files will be added to the repository at the next commit. To
    undo an add before that, see :hg:`forget`.

    If no names are given, add all files to the repository (except
    files matching ``.hgignore``).

    .. container:: verbose

       Examples:

         - New (unknown) files are added
           automatically by :hg:`add`::

             $ ls
             foo.c
             $ hg status
             ? foo.c
             $ hg add
             adding foo.c
             $ hg status
             A foo.c

         - Specific files to be added can be specified::

             $ ls
             bar.c  foo.c
             $ hg status
             ? bar.c
             ? foo.c
             $ hg add bar.c
             $ hg status
             A bar.c
             ? foo.c

    Returns 0 if all files are successfully added.
    """

    m = scmutil.match(repo[None], pats, opts)
    rejected = cmdutil.add(ui, repo, m, "", False, **opts)
    return rejected and 1 or 0

@command('addremove',
    similarityopts + subrepoopts + walkopts + dryrunopts,
    _('[OPTION]... [FILE]...'),
    inferrepo=True)
def addremove(ui, repo, *pats, **opts):
    """add all new files, delete all missing files

    Add all new files and remove all missing files from the
    repository.

    Unless names are given, new files are ignored if they match any of
    the patterns in ``.hgignore``. As with add, these changes take
    effect at the next commit.

    Use the -s/--similarity option to detect renamed files. This
    option takes a percentage between 0 (disabled) and 100 (files must
    be identical) as its parameter. With a parameter greater than 0,
    this compares every removed file with every added file and records
    those similar enough as renames. Detecting renamed files this way
    can be expensive. After using this option, :hg:`status -C` can be
    used to check which files were identified as moved or renamed. If
    not specified, -s/--similarity defaults to 100 and only renames of
    identical files are detected.

    .. container:: verbose

       Examples:

         - A number of files (bar.c and foo.c) are new,
           while foobar.c has been removed (without using :hg:`remove`)
           from the repository::

             $ ls
             bar.c foo.c
             $ hg status
             ! foobar.c
             ? bar.c
             ? foo.c
             $ hg addremove
             adding bar.c
             adding foo.c
             removing foobar.c
             $ hg status
             A bar.c
             A foo.c
             R foobar.c

         - A file foobar.c was moved to foo.c without using :hg:`rename`.
           Afterwards, it was edited slightly::

             $ ls
             foo.c
             $ hg status
             ! foobar.c
             ? foo.c
             $ hg addremove --similarity 90
             removing foobar.c
             adding foo.c
             recording removal of foobar.c as rename to foo.c (94% similar)
             $ hg status -C
             A foo.c
               foobar.c
             R foobar.c

    Returns 0 if all files are successfully added.
    """
    try:
        sim = float(opts.get('similarity') or 100)
    except ValueError:
        raise error.Abort(_('similarity must be a number'))
    if sim < 0 or sim > 100:
        raise error.Abort(_('similarity must be between 0 and 100'))
    matcher = scmutil.match(repo[None], pats, opts)
    return scmutil.addremove(repo, matcher, "", opts, similarity=sim / 100.0)

@command('^annotate|blame',
    [('r', 'rev', '', _('annotate the specified revision'), _('REV')),
    ('', 'follow', None,
     _('follow copies/renames and list the filename (DEPRECATED)')),
    ('', 'no-follow', None, _("don't follow copies and renames")),
    ('a', 'text', None, _('treat all files as text')),
    ('u', 'user', None, _('list the author (long with -v)')),
    ('f', 'file', None, _('list the filename')),
    ('d', 'date', None, _('list the date (short with -q)')),
    ('n', 'number', None, _('list the revision number (default)')),
    ('c', 'changeset', None, _('list the changeset')),
    ('l', 'line-number', None, _('show line number at the first appearance'))
    ] + diffwsopts + walkopts + formatteropts,
    _('[-r REV] [-f] [-a] [-u] [-d] [-n] [-c] [-l] FILE...'),
    inferrepo=True)
def annotate(ui, repo, *pats, **opts):
    """show changeset information by line for each file

    List changes in files, showing the revision id responsible for
    each line.

    This command is useful for discovering when a change was made and
    by whom.

    If you include --file, --user, or --date, the revision number is
    suppressed unless you also include --number.

    Without the -a/--text option, annotate will avoid processing files
    it detects as binary. With -a, annotate will annotate the file
    anyway, although the results will probably be neither useful
    nor desirable.

    Returns 0 on success.
    """
    if not pats:
        raise error.Abort(_('at least one filename or pattern is required'))

    if opts.get('follow'):
        # --follow is deprecated and now just an alias for -f/--file
        # to mimic the behavior of Mercurial before version 1.5
        opts['file'] = True

    ctx = scmutil.revsingle(repo, opts.get('rev'))

    fm = ui.formatter('annotate', opts)
    if ui.quiet:
        datefunc = util.shortdate
    else:
        datefunc = util.datestr
    if ctx.rev() is None:
        def hexfn(node):
            if node is None:
                return None
            else:
                return fm.hexfunc(node)
        if opts.get('changeset'):
            # omit "+" suffix which is appended to node hex
            def formatrev(rev):
                if rev is None:
                    return '%d' % ctx.p1().rev()
                else:
                    return '%d' % rev
        else:
            def formatrev(rev):
                if rev is None:
                    return '%d+' % ctx.p1().rev()
                else:
                    return '%d ' % rev
        def formathex(hex):
            if hex is None:
                return '%s+' % fm.hexfunc(ctx.p1().node())
            else:
                return '%s ' % hex
    else:
        hexfn = fm.hexfunc
        formatrev = formathex = str

    opmap = [('user', ' ', lambda x: x[0].user(), ui.shortuser),
             ('number', ' ', lambda x: x[0].rev(), formatrev),
             ('changeset', ' ', lambda x: hexfn(x[0].node()), formathex),
             ('date', ' ', lambda x: x[0].date(), util.cachefunc(datefunc)),
             ('file', ' ', lambda x: x[0].path(), str),
             ('line_number', ':', lambda x: x[1], str),
            ]
    fieldnamemap = {'number': 'rev', 'changeset': 'node'}

    if (not opts.get('user') and not opts.get('changeset')
        and not opts.get('date') and not opts.get('file')):
        opts['number'] = True

    linenumber = opts.get('line_number') is not None
    if linenumber and (not opts.get('changeset')) and (not opts.get('number')):
        raise error.Abort(_('at least one of -n/-c is required for -l'))

    if fm.isplain():
        def makefunc(get, fmt):
            return lambda x: fmt(get(x))
    else:
        def makefunc(get, fmt):
            return get
    funcmap = [(makefunc(get, fmt), sep) for op, sep, get, fmt in opmap
               if opts.get(op)]
    funcmap[0] = (funcmap[0][0], '') # no separator in front of first column
    fields = ' '.join(fieldnamemap.get(op, op) for op, sep, get, fmt in opmap
                      if opts.get(op))

    def bad(x, y):
        raise error.Abort("%s: %s" % (x, y))

    m = scmutil.match(ctx, pats, opts, badfn=bad)

    follow = not opts.get('no_follow')
    diffopts = patch.difffeatureopts(ui, opts, section='annotate',
                                     whitespace=True)
    for abs in ctx.walk(m):
        fctx = ctx[abs]
        if not opts.get('text') and util.binary(fctx.data()):
            fm.plain(_("%s: binary file\n") % ((pats and m.rel(abs)) or abs))
            continue

        lines = fctx.annotate(follow=follow, linenumber=linenumber,
                              diffopts=diffopts)
        if not lines:
            continue
        formats = []
        pieces = []

        for f, sep in funcmap:
            l = [f(n) for n, dummy in lines]
            if fm.isplain():
                sizes = [encoding.colwidth(x) for x in l]
                ml = max(sizes)
                formats.append([sep + ' ' * (ml - w) + '%s' for w in sizes])
            else:
                formats.append(['%s' for x in l])
            pieces.append(l)

        for f, p, l in zip(zip(*formats), zip(*pieces), lines):
            fm.startitem()
            fm.write(fields, "".join(f), *p)
            fm.write('line', ": %s", l[1])

        if not lines[-1][1].endswith('\n'):
            fm.plain('\n')

    fm.end()

@command('archive',
    [('', 'no-decode', None, _('do not pass files through decoders')),
    ('p', 'prefix', '', _('directory prefix for files in archive'),
     _('PREFIX')),
    ('r', 'rev', '', _('revision to distribute'), _('REV')),
    ('t', 'type', '', _('type of distribution to create'), _('TYPE')),
    ] + subrepoopts + walkopts,
    _('[OPTION]... DEST'))
def archive(ui, repo, dest, **opts):
    '''create an unversioned archive of a repository revision

    By default, the revision used is the parent of the working
    directory; use -r/--rev to specify a different revision.

    The archive type is automatically detected based on file
    extension (to override, use -t/--type).

    .. container:: verbose

      Examples:

      - create a zip file containing the 1.0 release::

          hg archive -r 1.0 project-1.0.zip

      - create a tarball excluding .hg files::

          hg archive project.tar.gz -X ".hg*"

    Valid types are:

    :``files``: a directory full of files (default)
    :``tar``:   tar archive, uncompressed
    :``tbz2``:  tar archive, compressed using bzip2
    :``tgz``:   tar archive, compressed using gzip
    :``uzip``:  zip archive, uncompressed
    :``zip``:   zip archive, compressed using deflate

    The exact name of the destination archive or directory is given
    using a format string; see :hg:`help export` for details.

    Each member added to an archive file has a directory prefix
    prepended. Use -p/--prefix to specify a format string for the
    prefix. The default is the basename of the archive, with suffixes
    removed.

    Returns 0 on success.
    '''

    ctx = scmutil.revsingle(repo, opts.get('rev'))
    if not ctx:
        raise error.Abort(_('no working directory: please specify a revision'))
    node = ctx.node()
    dest = cmdutil.makefilename(repo, dest, node)
    if os.path.realpath(dest) == repo.root:
        raise error.Abort(_('repository root cannot be destination'))

    kind = opts.get('type') or archival.guesskind(dest) or 'files'
    prefix = opts.get('prefix')

    if dest == '-':
        if kind == 'files':
            raise error.Abort(_('cannot archive plain files to stdout'))
        dest = cmdutil.makefileobj(repo, dest)
        if not prefix:
            prefix = os.path.basename(repo.root) + '-%h'

    prefix = cmdutil.makefilename(repo, prefix, node)
    matchfn = scmutil.match(ctx, [], opts)
    archival.archive(repo, dest, node, kind, not opts.get('no_decode'),
                     matchfn, prefix, subrepos=opts.get('subrepos'))

@command('backout',
    [('', 'merge', None, _('merge with old dirstate parent after backout')),
    ('', 'commit', None,
     _('commit if no conflicts were encountered (DEPRECATED)')),
    ('', 'no-commit', None, _('do not commit')),
    ('', 'parent', '',
     _('parent to choose when backing out merge (DEPRECATED)'), _('REV')),
    ('r', 'rev', '', _('revision to backout'), _('REV')),
    ('e', 'edit', False, _('invoke editor on commit messages')),
    ] + mergetoolopts + walkopts + commitopts + commitopts2,
    _('[OPTION]... [-r] REV'))
def backout(ui, repo, node=None, rev=None, **opts):
    '''reverse effect of earlier changeset

    Prepare a new changeset with the effect of REV undone in the
    current working directory. If no conflicts were encountered,
    it will be committed immediately.

    If REV is the parent of the working directory, then this new changeset
    is committed automatically (unless --no-commit is specified).

    .. note::

       :hg:`backout` cannot be used to fix either an unwanted or
       incorrect merge.

    .. container:: verbose

      Examples:

      - Reverse the effect of the parent of the working directory.
        This backout will be committed immediately::

          hg backout -r .

      - Reverse the effect of previous bad revision 23::

          hg backout -r 23

      - Reverse the effect of previous bad revision 23 and
        leave changes uncommitted::

          hg backout -r 23 --no-commit
          hg commit -m "Backout revision 23"

      By default, the pending changeset will have one parent,
      maintaining a linear history. With --merge, the pending
      changeset will instead have two parents: the old parent of the
      working directory and a new child of REV that simply undoes REV.

      Before version 1.7, the behavior without --merge was equivalent
      to specifying --merge followed by :hg:`update --clean .` to
      cancel the merge and leave the child of REV as a head to be
      merged separately.

    See :hg:`help dates` for a list of formats valid for -d/--date.

    See :hg:`help revert` for a way to restore files to the state
    of another revision.

    Returns 0 on success, 1 if nothing to backout or there are unresolved
    files.
    '''
    wlock = lock = None
    try:
        wlock = repo.wlock()
        lock = repo.lock()
        return _dobackout(ui, repo, node, rev, **opts)
    finally:
        release(lock, wlock)

def _dobackout(ui, repo, node=None, rev=None, **opts):
    if opts.get('commit') and opts.get('no_commit'):
        raise error.Abort(_("cannot use --commit with --no-commit"))
    if opts.get('merge') and opts.get('no_commit'):
        raise error.Abort(_("cannot use --merge with --no-commit"))

    if rev and node:
        raise error.Abort(_("please specify just one revision"))

    if not rev:
        rev = node

    if not rev:
        raise error.Abort(_("please specify a revision to backout"))

    date = opts.get('date')
    if date:
        opts['date'] = util.parsedate(date)

    cmdutil.checkunfinished(repo)
    cmdutil.bailifchanged(repo)
    node = scmutil.revsingle(repo, rev).node()

    op1, op2 = repo.dirstate.parents()
    if not repo.changelog.isancestor(node, op1):
        raise error.Abort(_('cannot backout change that is not an ancestor'))

    p1, p2 = repo.changelog.parents(node)
    if p1 == nullid:
        raise error.Abort(_('cannot backout a change with no parents'))
    if p2 != nullid:
        if not opts.get('parent'):
            raise error.Abort(_('cannot backout a merge changeset'))
        p = repo.lookup(opts['parent'])
        if p not in (p1, p2):
            raise error.Abort(_('%s is not a parent of %s') %
                             (short(p), short(node)))
        parent = p
    else:
        if opts.get('parent'):
            raise error.Abort(_('cannot use --parent on non-merge changeset'))
        parent = p1

    # the backout should appear on the same branch
    branch = repo.dirstate.branch()
    bheads = repo.branchheads(branch)
    rctx = scmutil.revsingle(repo, hex(parent))
    if not opts.get('merge') and op1 != node:
        dsguard = cmdutil.dirstateguard(repo, 'backout')
        try:
            ui.setconfig('ui', 'forcemerge', opts.get('tool', ''),
                         'backout')
            stats = mergemod.update(repo, parent, True, True, node, False)
            repo.setparents(op1, op2)
            dsguard.close()
            hg._showstats(repo, stats)
            if stats[3]:
                repo.ui.status(_("use 'hg resolve' to retry unresolved "
                                 "file merges\n"))
                return 1
        finally:
            ui.setconfig('ui', 'forcemerge', '', '')
            lockmod.release(dsguard)
    else:
        hg.clean(repo, node, show_stats=False)
        repo.dirstate.setbranch(branch)
        cmdutil.revert(ui, repo, rctx, repo.dirstate.parents())

    if opts.get('no_commit'):
        msg = _("changeset %s backed out, "
                "don't forget to commit.\n")
        ui.status(msg % short(node))
        return 0

    def commitfunc(ui, repo, message, match, opts):
        editform = 'backout'
        e = cmdutil.getcommiteditor(editform=editform, **opts)
        if not message:
            # we don't translate commit messages
            message = "Backed out changeset %s" % short(node)
            e = cmdutil.getcommiteditor(edit=True, editform=editform)
        return repo.commit(message, opts.get('user'), opts.get('date'),
                           match, editor=e)
    newnode = cmdutil.commit(ui, repo, commitfunc, [], opts)
    if not newnode:
        ui.status(_("nothing changed\n"))
        return 1
    cmdutil.commitstatus(repo, newnode, branch, bheads)

    def nice(node):
        return '%d:%s' % (repo.changelog.rev(node), short(node))
    ui.status(_('changeset %s backs out changeset %s\n') %
              (nice(repo.changelog.tip()), nice(node)))
    if opts.get('merge') and op1 != node:
        hg.clean(repo, op1, show_stats=False)
        ui.status(_('merging with changeset %s\n')
                  % nice(repo.changelog.tip()))
        try:
            ui.setconfig('ui', 'forcemerge', opts.get('tool', ''),
                         'backout')
            return hg.merge(repo, hex(repo.changelog.tip()))
        finally:
            ui.setconfig('ui', 'forcemerge', '', '')
    return 0

@command('bisect',
    [('r', 'reset', False, _('reset bisect state')),
    ('g', 'good', False, _('mark changeset good')),
    ('b', 'bad', False, _('mark changeset bad')),
    ('s', 'skip', False, _('skip testing changeset')),
    ('e', 'extend', False, _('extend the bisect range')),
    ('c', 'command', '', _('use command to check changeset state'), _('CMD')),
    ('U', 'noupdate', False, _('do not update to target'))],
    _("[-gbsr] [-U] [-c CMD] [REV]"))
def bisect(ui, repo, rev=None, extra=None, command=None,
               reset=None, good=None, bad=None, skip=None, extend=None,
               noupdate=None):
    """subdivision search of changesets

    This command helps to find changesets which introduce problems. To
    use, mark the earliest changeset you know exhibits the problem as
    bad, then mark the latest changeset which is free from the problem
    as good. Bisect will update your working directory to a revision
    for testing (unless the -U/--noupdate option is specified). Once
    you have performed tests, mark the working directory as good or
    bad, and bisect will either update to another candidate changeset
    or announce that it has found the bad revision.

    As a shortcut, you can also use the revision argument to mark a
    revision as good or bad without checking it out first.

    If you supply a command, it will be used for automatic bisection.
    The environment variable HG_NODE will contain the ID of the
    changeset being tested. The exit status of the command will be
    used to mark revisions as good or bad: status 0 means good, 125
    means to skip the revision, 127 (command not found) will abort the
    bisection, and any other non-zero exit status means the revision
    is bad.

    .. container:: verbose

      Some examples:

      - start a bisection with known bad revision 34, and good revision 12::

          hg bisect --bad 34
          hg bisect --good 12

      - advance the current bisection by marking current revision as good or
        bad::

          hg bisect --good
          hg bisect --bad

      - mark the current revision, or a known revision, to be skipped (e.g. if
        that revision is not usable because of another issue)::

          hg bisect --skip
          hg bisect --skip 23

      - skip all revisions that do not touch directories ``foo`` or ``bar``::

          hg bisect --skip "!( file('path:foo') & file('path:bar') )"

      - forget the current bisection::

          hg bisect --reset

      - use 'make && make tests' to automatically find the first broken
        revision::

          hg bisect --reset
          hg bisect --bad 34
          hg bisect --good 12
          hg bisect --command "make && make tests"

      - see all changesets whose states are already known in the current
        bisection::

          hg log -r "bisect(pruned)"

      - see the changeset currently being bisected (especially useful
        if running with -U/--noupdate)::

          hg log -r "bisect(current)"

      - see all changesets that took part in the current bisection::

          hg log -r "bisect(range)"

      - you can even get a nice graph::

          hg log --graph -r "bisect(range)"

      See :hg:`help revsets` for more about the `bisect()` keyword.

    Returns 0 on success.
    """
    # backward compatibility
    if rev in "good bad reset init".split():
        ui.warn(_("(use of 'hg bisect <cmd>' is deprecated)\n"))
        cmd, rev, extra = rev, extra, None
        if cmd == "good":
            good = True
        elif cmd == "bad":
            bad = True
        else:
            reset = True
    elif extra or good + bad + skip + reset + extend + bool(command) > 1:
        raise error.Abort(_('incompatible arguments'))

    cmdutil.checkunfinished(repo)

    if reset:
        hbisect.resetstate(repo)
        return

    state = hbisect.load_state(repo)

    # update state
    if good or bad or skip:
        if rev:
            nodes = [repo.lookup(i) for i in scmutil.revrange(repo, [rev])]
        else:
            nodes = [repo.lookup('.')]
        if good:
            state['good'] += nodes
        elif bad:
            state['bad'] += nodes
        elif skip:
            state['skip'] += nodes
        hbisect.save_state(repo, state)
        if not (state['good'] and state['bad']):
            return

    def mayupdate(repo, node, show_stats=True):
        """common used update sequence"""
        if noupdate:
            return
        cmdutil.bailifchanged(repo)
        return hg.clean(repo, node, show_stats=show_stats)

    displayer = cmdutil.show_changeset(ui, repo, {})

    if command:
        changesets = 1
        if noupdate:
            try:
                node = state['current'][0]
            except LookupError:
                raise error.Abort(_('current bisect revision is unknown - '
                                   'start a new bisect to fix'))
        else:
            node, p2 = repo.dirstate.parents()
            if p2 != nullid:
                raise error.Abort(_('current bisect revision is a merge'))
        if rev:
            node = repo[scmutil.revsingle(repo, rev, node)].node()
        try:
            while changesets:
                # update state
                state['current'] = [node]
                hbisect.save_state(repo, state)
                status = ui.system(command, environ={'HG_NODE': hex(node)})
                if status == 125:
                    transition = "skip"
                elif status == 0:
                    transition = "good"
                # status < 0 means process was killed
                elif status == 127:
                    raise error.Abort(_("failed to execute %s") % command)
                elif status < 0:
                    raise error.Abort(_("%s killed") % command)
                else:
                    transition = "bad"
                state[transition].append(node)
                ctx = repo[node]
                ui.status(_('changeset %d:%s: %s\n') % (ctx, ctx, transition))
                hbisect.checkstate(state)
                # bisect
                nodes, changesets, bgood = hbisect.bisect(repo.changelog, state)
                # update to next check
                node = nodes[0]
                mayupdate(repo, node, show_stats=False)
        finally:
            state['current'] = [node]
            hbisect.save_state(repo, state)
        hbisect.printresult(ui, repo, state, displayer, nodes, bgood)
        return

    hbisect.checkstate(state)

    # actually bisect
    nodes, changesets, good = hbisect.bisect(repo.changelog, state)
    if extend:
        if not changesets:
            extendnode = hbisect.extendrange(repo, state, nodes, good)
            if extendnode is not None:
                ui.write(_("Extending search to changeset %d:%s\n")
                         % (extendnode.rev(), extendnode))
                state['current'] = [extendnode.node()]
                hbisect.save_state(repo, state)
                return mayupdate(repo, extendnode.node())
        raise error.Abort(_("nothing to extend"))

    if changesets == 0:
        hbisect.printresult(ui, repo, state, displayer, nodes, good)
    else:
        assert len(nodes) == 1 # only a single node can be tested next
        node = nodes[0]
        # compute the approximate number of remaining tests
        tests, size = 0, 2
        while size <= changesets:
            tests, size = tests + 1, size * 2
        rev = repo.changelog.rev(node)
        ui.write(_("Testing changeset %d:%s "
                   "(%d changesets remaining, ~%d tests)\n")
                 % (rev, short(node), changesets, tests))
        state['current'] = [node]
        hbisect.save_state(repo, state)
        return mayupdate(repo, node)

@command('bookmarks|bookmark',
    [('f', 'force', False, _('force')),
    ('r', 'rev', '', _('revision for bookmark action'), _('REV')),
    ('d', 'delete', False, _('delete a given bookmark')),
    ('m', 'rename', '', _('rename a given bookmark'), _('OLD')),
    ('i', 'inactive', False, _('mark a bookmark inactive')),
    ] + formatteropts,
    _('hg bookmarks [OPTIONS]... [NAME]...'))
def bookmark(ui, repo, *names, **opts):
    '''create a new bookmark or list existing bookmarks

    Bookmarks are labels on changesets to help track lines of development.
    Bookmarks are unversioned and can be moved, renamed and deleted.
    Deleting or moving a bookmark has no effect on the associated changesets.

    Creating or updating to a bookmark causes it to be marked as 'active'.
    The active bookmark is indicated with a '*'.
    When a commit is made, the active bookmark will advance to the new commit.
    A plain :hg:`update` will also advance an active bookmark, if possible.
    Updating away from a bookmark will cause it to be deactivated.

    Bookmarks can be pushed and pulled between repositories (see
    :hg:`help push` and :hg:`help pull`). If a shared bookmark has
    diverged, a new 'divergent bookmark' of the form 'name@path' will
    be created. Using :hg:`merge` will resolve the divergence.

    A bookmark named '@' has the special property that :hg:`clone` will
    check it out by default if it exists.

    .. container:: verbose

      Examples:

      - create an active bookmark for a new line of development::

          hg book new-feature

      - create an inactive bookmark as a place marker::

          hg book -i reviewed

      - create an inactive bookmark on another changeset::

          hg book -r .^ tested

      - rename bookmark turkey to dinner::

          hg book -m turkey dinner

      - move the '@' bookmark from another branch::

          hg book -f @
    '''
    force = opts.get('force')
    rev = opts.get('rev')
    delete = opts.get('delete')
    rename = opts.get('rename')
    inactive = opts.get('inactive')

    def checkformat(mark):
        mark = mark.strip()
        if not mark:
            raise error.Abort(_("bookmark names cannot consist entirely of "
                               "whitespace"))
        scmutil.checknewlabel(repo, mark, 'bookmark')
        return mark

    def checkconflict(repo, mark, cur, force=False, target=None):
        if mark in marks and not force:
            if target:
                if marks[mark] == target and target == cur:
                    # re-activating a bookmark
                    return
                anc = repo.changelog.ancestors([repo[target].rev()])
                bmctx = repo[marks[mark]]
                divs = [repo[b].node() for b in marks
                        if b.split('@', 1)[0] == mark.split('@', 1)[0]]

                # allow resolving a single divergent bookmark even if moving
                # the bookmark across branches when a revision is specified
                # that contains a divergent bookmark
                if bmctx.rev() not in anc and target in divs:
                    bookmarks.deletedivergent(repo, [target], mark)
                    return

                deletefrom = [b for b in divs
                              if repo[b].rev() in anc or b == target]
                bookmarks.deletedivergent(repo, deletefrom, mark)
                if bookmarks.validdest(repo, bmctx, repo[target]):
                    ui.status(_("moving bookmark '%s' forward from %s\n") %
                              (mark, short(bmctx.node())))
                    return
            raise error.Abort(_("bookmark '%s' already exists "
                               "(use -f to force)") % mark)
        if ((mark in repo.branchmap() or mark == repo.dirstate.branch())
            and not force):
            raise error.Abort(
                _("a bookmark cannot have the name of an existing branch"))

    if delete and rename:
        raise error.Abort(_("--delete and --rename are incompatible"))
    if delete and rev:
        raise error.Abort(_("--rev is incompatible with --delete"))
    if rename and rev:
        raise error.Abort(_("--rev is incompatible with --rename"))
    if not names and (delete or rev):
        raise error.Abort(_("bookmark name required"))

    if delete or rename or names or inactive:
        wlock = lock = tr = None
        try:
            wlock = repo.wlock()
            lock = repo.lock()
            cur = repo.changectx('.').node()
            marks = repo._bookmarks
            if delete:
                tr = repo.transaction('bookmark')
                for mark in names:
                    if mark not in marks:
                        raise error.Abort(_("bookmark '%s' does not exist") %
                                         mark)
                    if mark == repo._activebookmark:
                        bookmarks.deactivate(repo)
                    del marks[mark]

            elif rename:
                tr = repo.transaction('bookmark')
                if not names:
                    raise error.Abort(_("new bookmark name required"))
                elif len(names) > 1:
                    raise error.Abort(_("only one new bookmark name allowed"))
                mark = checkformat(names[0])
                if rename not in marks:
                    raise error.Abort(_("bookmark '%s' does not exist")
                                      % rename)
                checkconflict(repo, mark, cur, force)
                marks[mark] = marks[rename]
                if repo._activebookmark == rename and not inactive:
                    bookmarks.activate(repo, mark)
                del marks[rename]
            elif names:
                tr = repo.transaction('bookmark')
                newact = None
                for mark in names:
                    mark = checkformat(mark)
                    if newact is None:
                        newact = mark
                    if inactive and mark == repo._activebookmark:
                        bookmarks.deactivate(repo)
                        return
                    tgt = cur
                    if rev:
                        tgt = scmutil.revsingle(repo, rev).node()
                    checkconflict(repo, mark, cur, force, tgt)
                    marks[mark] = tgt
                if not inactive and cur == marks[newact] and not rev:
                    bookmarks.activate(repo, newact)
                elif cur != tgt and newact == repo._activebookmark:
                    bookmarks.deactivate(repo)
            elif inactive:
                if len(marks) == 0:
                    ui.status(_("no bookmarks set\n"))
                elif not repo._activebookmark:
                    ui.status(_("no active bookmark\n"))
                else:
                    bookmarks.deactivate(repo)
            if tr is not None:
                marks.recordchange(tr)
                tr.close()
        finally:
            lockmod.release(tr, lock, wlock)
    else: # show bookmarks
        fm = ui.formatter('bookmarks', opts)
        hexfn = fm.hexfunc
        marks = repo._bookmarks
        if len(marks) == 0 and fm.isplain():
            ui.status(_("no bookmarks set\n"))
        for bmark, n in sorted(marks.iteritems()):
            active = repo._activebookmark
            if bmark == active:
                prefix, label = '*', activebookmarklabel
            else:
                prefix, label = ' ', ''

            fm.startitem()
            if not ui.quiet:
                fm.plain(' %s ' % prefix, label=label)
            fm.write('bookmark', '%s', bmark, label=label)
            pad = " " * (25 - encoding.colwidth(bmark))
            fm.condwrite(not ui.quiet, 'rev node', pad + ' %d:%s',
                         repo.changelog.rev(n), hexfn(n), label=label)
            fm.data(active=(bmark == active))
            fm.plain('\n')
        fm.end()

@command('branch',
    [('f', 'force', None,
     _('set branch name even if it shadows an existing branch')),
    ('C', 'clean', None, _('reset branch name to parent branch name'))],
    _('[-fC] [NAME]'))
def branch(ui, repo, label=None, **opts):
    """set or show the current branch name

    .. note::

       Branch names are permanent and global. Use :hg:`bookmark` to create a
       light-weight bookmark instead. See :hg:`help glossary` for more
       information about named branches and bookmarks.

    With no argument, show the current branch name. With one argument,
    set the working directory branch name (the branch will not exist
    in the repository until the next commit). Standard practice
    recommends that primary development take place on the 'default'
    branch.

    Unless -f/--force is specified, branch will not let you set a
    branch name that already exists.

    Use -C/--clean to reset the working directory branch to that of
    the parent of the working directory, negating a previous branch
    change.

    Use the command :hg:`update` to switch to an existing branch. Use
    :hg:`commit --close-branch` to mark this branch head as closed.
    When all heads of a branch are closed, the branch will be
    considered closed.

    Returns 0 on success.
    """
    if label:
        label = label.strip()

    if not opts.get('clean') and not label:
        ui.write("%s\n" % repo.dirstate.branch())
        return

    with repo.wlock():
        if opts.get('clean'):
            label = repo[None].p1().branch()
            repo.dirstate.setbranch(label)
            ui.status(_('reset working directory to branch %s\n') % label)
        elif label:
            if not opts.get('force') and label in repo.branchmap():
                if label not in [p.branch() for p in repo[None].parents()]:
                    raise error.Abort(_('a branch of the same name already'
                                       ' exists'),
                                     # i18n: "it" refers to an existing branch
                                     hint=_("use 'hg update' to switch to it"))
            scmutil.checknewlabel(repo, label, 'branch')
            repo.dirstate.setbranch(label)
            ui.status(_('marked working directory as branch %s\n') % label)

            # find any open named branches aside from default
            others = [n for n, h, t, c in repo.branchmap().iterbranches()
                      if n != "default" and not c]
            if not others:
                ui.status(_('(branches are permanent and global, '
                            'did you want a bookmark?)\n'))

@command('branches',
    [('a', 'active', False,
      _('show only branches that have unmerged heads (DEPRECATED)')),
     ('c', 'closed', False, _('show normal and closed branches')),
    ] + formatteropts,
    _('[-c]'))
def branches(ui, repo, active=False, closed=False, **opts):
    """list repository named branches

    List the repository's named branches, indicating which ones are
    inactive. If -c/--closed is specified, also list branches which have
    been marked closed (see :hg:`commit --close-branch`).

    Use the command :hg:`update` to switch to an existing branch.

    Returns 0.
    """

    fm = ui.formatter('branches', opts)
    hexfunc = fm.hexfunc

    allheads = set(repo.heads())
    branches = []
    for tag, heads, tip, isclosed in repo.branchmap().iterbranches():
        isactive = not isclosed and bool(set(heads) & allheads)
        branches.append((tag, repo[tip], isactive, not isclosed))
    branches.sort(key=lambda i: (i[2], i[1].rev(), i[0], i[3]),
                  reverse=True)

    for tag, ctx, isactive, isopen in branches:
        if active and not isactive:
            continue
        if isactive:
            label = 'branches.active'
            notice = ''
        elif not isopen:
            if not closed:
                continue
            label = 'branches.closed'
            notice = _(' (closed)')
        else:
            label = 'branches.inactive'
            notice = _(' (inactive)')
        current = (tag == repo.dirstate.branch())
        if current:
            label = 'branches.current'

        fm.startitem()
        fm.write('branch', '%s', tag, label=label)
        rev = ctx.rev()
        padsize = max(31 - len(str(rev)) - encoding.colwidth(tag), 0)
        fmt = ' ' * padsize + ' %d:%s'
        fm.condwrite(not ui.quiet, 'rev node', fmt, rev, hexfunc(ctx.node()),
                     label='log.changeset changeset.%s' % ctx.phasestr())
        fm.data(active=isactive, closed=not isopen, current=current)
        if not ui.quiet:
            fm.plain(notice)
        fm.plain('\n')
    fm.end()

@command('bundle',
    [('f', 'force', None, _('run even when the destination is unrelated')),
    ('r', 'rev', [], _('a changeset intended to be added to the destination'),
     _('REV')),
    ('b', 'branch', [], _('a specific branch you would like to bundle'),
     _('BRANCH')),
    ('', 'base', [],
     _('a base changeset assumed to be available at the destination'),
     _('REV')),
    ('a', 'all', None, _('bundle all changesets in the repository')),
    ('t', 'type', 'bzip2', _('bundle compression type to use'), _('TYPE')),
    ] + remoteopts,
    _('[-f] [-t TYPE] [-a] [-r REV]... [--base REV]... FILE [DEST]'))
def bundle(ui, repo, fname, dest=None, **opts):
    """create a changegroup file

    Generate a changegroup file collecting changesets to be added
    to a repository.

    To create a bundle containing all changesets, use -a/--all
    (or --base null). Otherwise, hg assumes the destination will have
    all the nodes you specify with --base parameters. Otherwise, hg
    will assume the repository has all the nodes in destination, or
    default-push/default if no destination is specified.

    You can change bundle format with the -t/--type option. You can
    specify a compression, a bundle version or both using a dash
    (comp-version). The available compression methods are: none, bzip2,
    and gzip (by default, bundles are compressed using bzip2). The
    available formats are: v1, v2 (default to most suitable).

    The bundle file can then be transferred using conventional means
    and applied to another repository with the unbundle or pull
    command. This is useful when direct push and pull are not
    available or when exporting an entire repository is undesirable.

    Applying bundles preserves all changeset contents including
    permissions, copy/rename information, and revision history.

    Returns 0 on success, 1 if no changes found.
    """
    revs = None
    if 'rev' in opts:
        revstrings = opts['rev']
        revs = scmutil.revrange(repo, revstrings)
        if revstrings and not revs:
            raise error.Abort(_('no commits to bundle'))

    bundletype = opts.get('type', 'bzip2').lower()
    try:
        bcompression, cgversion, params = exchange.parsebundlespec(
                repo, bundletype, strict=False)
    except error.UnsupportedBundleSpecification as e:
        raise error.Abort(str(e),
                          hint=_("see 'hg help bundle' for supported "
                                 "values for --type"))

    # Packed bundles are a pseudo bundle format for now.
    if cgversion == 's1':
        raise error.Abort(_('packed bundles cannot be produced by "hg bundle"'),
                          hint=_("use 'hg debugcreatestreamclonebundle'"))

    if opts.get('all'):
        if dest:
            raise error.Abort(_("--all is incompatible with specifying "
                                "a destination"))
        if opts.get('base'):
            ui.warn(_("ignoring --base because --all was specified\n"))
        base = ['null']
    else:
        base = scmutil.revrange(repo, opts.get('base'))
    # TODO: get desired bundlecaps from command line.
    bundlecaps = None
    if cgversion not in changegroup.supportedoutgoingversions(repo):
        raise error.Abort(_("repository does not support bundle version %s") %
                          cgversion)

    if base:
        if dest:
            raise error.Abort(_("--base is incompatible with specifying "
                               "a destination"))
        common = [repo.lookup(rev) for rev in base]
        heads = revs and map(repo.lookup, revs) or None
        outgoing = discovery.outgoing(repo, common, heads)
        cg = changegroup.getchangegroup(repo, 'bundle', outgoing,
                                        bundlecaps=bundlecaps,
                                        version=cgversion)
        outgoing = None
    else:
        dest = ui.expandpath(dest or 'default-push', dest or 'default')
        dest, branches = hg.parseurl(dest, opts.get('branch'))
        other = hg.peer(repo, opts, dest)
        revs, checkout = hg.addbranchrevs(repo, repo, branches, revs)
        heads = revs and map(repo.lookup, revs) or revs
        outgoing = discovery.findcommonoutgoing(repo, other,
                                                onlyheads=heads,
                                                force=opts.get('force'),
                                                portable=True)
        cg = changegroup.getlocalchangegroup(repo, 'bundle', outgoing,
                                                bundlecaps, version=cgversion)
    if not cg:
        scmutil.nochangesfound(ui, repo, outgoing and outgoing.excluded)
        return 1

    if cgversion == '01': #bundle1
        if bcompression is None:
            bcompression = 'UN'
        bversion = 'HG10' + bcompression
        bcompression = None
    else:
        assert cgversion == '02'
        bversion = 'HG20'

    bundle2.writebundle(ui, cg, fname, bversion, compression=bcompression)

@command('cat',
    [('o', 'output', '',
     _('print output to file with formatted name'), _('FORMAT')),
    ('r', 'rev', '', _('print the given revision'), _('REV')),
    ('', 'decode', None, _('apply any matching decode filter')),
    ] + walkopts,
    _('[OPTION]... FILE...'),
    inferrepo=True)
def cat(ui, repo, file1, *pats, **opts):
    """output the current or given revision of files

    Print the specified files as they were at the given revision. If
    no revision is given, the parent of the working directory is used.

    Output may be to a file, in which case the name of the file is
    given using a format string. The formatting rules as follows:

    :``%%``: literal "%" character
    :``%s``: basename of file being printed
    :``%d``: dirname of file being printed, or '.' if in repository root
    :``%p``: root-relative path name of file being printed
    :``%H``: changeset hash (40 hexadecimal digits)
    :``%R``: changeset revision number
    :``%h``: short-form changeset hash (12 hexadecimal digits)
    :``%r``: zero-padded changeset revision number
    :``%b``: basename of the exporting repository

    Returns 0 on success.
    """
    ctx = scmutil.revsingle(repo, opts.get('rev'))
    m = scmutil.match(ctx, (file1,) + pats, opts)

    return cmdutil.cat(ui, repo, ctx, m, '', **opts)

@command('^clone',
    [('U', 'noupdate', None, _('the clone will include an empty working '
                               'directory (only a repository)')),
    ('u', 'updaterev', '', _('revision, tag, or branch to check out'),
        _('REV')),
    ('r', 'rev', [], _('include the specified changeset'), _('REV')),
    ('b', 'branch', [], _('clone only the specified branch'), _('BRANCH')),
    ('', 'pull', None, _('use pull protocol to copy metadata')),
    ('', 'uncompressed', None, _('use uncompressed transfer (fast over LAN)')),
    ] + remoteopts,
    _('[OPTION]... SOURCE [DEST]'),
    norepo=True)
def clone(ui, source, dest=None, **opts):
    """make a copy of an existing repository

    Create a copy of an existing repository in a new directory.

    If no destination directory name is specified, it defaults to the
    basename of the source.

    The location of the source is added to the new repository's
    ``.hg/hgrc`` file, as the default to be used for future pulls.

    Only local paths and ``ssh://`` URLs are supported as
    destinations. For ``ssh://`` destinations, no working directory or
    ``.hg/hgrc`` will be created on the remote side.

    If the source repository has a bookmark called '@' set, that
    revision will be checked out in the new repository by default.

    To check out a particular version, use -u/--update, or
    -U/--noupdate to create a clone with no working directory.

    To pull only a subset of changesets, specify one or more revisions
    identifiers with -r/--rev or branches with -b/--branch. The
    resulting clone will contain only the specified changesets and
    their ancestors. These options (or 'clone src#rev dest') imply
    --pull, even for local source repositories.

    .. note::

       Specifying a tag will include the tagged changeset but not the
       changeset containing the tag.

    .. container:: verbose

      For efficiency, hardlinks are used for cloning whenever the
      source and destination are on the same filesystem (note this
      applies only to the repository data, not to the working
      directory). Some filesystems, such as AFS, implement hardlinking
      incorrectly, but do not report errors. In these cases, use the
      --pull option to avoid hardlinking.

      In some cases, you can clone repositories and the working
      directory using full hardlinks with ::

        $ cp -al REPO REPOCLONE

      This is the fastest way to clone, but it is not always safe. The
      operation is not atomic (making sure REPO is not modified during
      the operation is up to you) and you have to make sure your
      editor breaks hardlinks (Emacs and most Linux Kernel tools do
      so). Also, this is not compatible with certain extensions that
      place their metadata under the .hg directory, such as mq.

      Mercurial will update the working directory to the first applicable
      revision from this list:

      a) null if -U or the source repository has no changesets
      b) if -u . and the source repository is local, the first parent of
         the source repository's working directory
      c) the changeset specified with -u (if a branch name, this means the
         latest head of that branch)
      d) the changeset specified with -r
      e) the tipmost head specified with -b
      f) the tipmost head specified with the url#branch source syntax
      g) the revision marked with the '@' bookmark, if present
      h) the tipmost head of the default branch
      i) tip

      When cloning from servers that support it, Mercurial may fetch
      pre-generated data from a server-advertised URL. When this is done,
      hooks operating on incoming changesets and changegroups may fire twice,
      once for the bundle fetched from the URL and another for any additional
      data not fetched from this URL. In addition, if an error occurs, the
      repository may be rolled back to a partial clone. This behavior may
      change in future releases. See :hg:`help -e clonebundles` for more.

      Examples:

      - clone a remote repository to a new directory named hg/::

          hg clone https://www.mercurial-scm.org/repo/hg/

      - create a lightweight local clone::

          hg clone project/ project-feature/

      - clone from an absolute path on an ssh server (note double-slash)::

          hg clone ssh://user@server//home/projects/alpha/

      - do a high-speed clone over a LAN while checking out a
        specified version::

          hg clone --uncompressed http://server/repo -u 1.5

      - create a repository without changesets after a particular revision::

          hg clone -r 04e544 experimental/ good/

      - clone (and track) a particular named branch::

          hg clone https://www.mercurial-scm.org/repo/hg/#stable

    See :hg:`help urls` for details on specifying URLs.

    Returns 0 on success.
    """
    if opts.get('noupdate') and opts.get('updaterev'):
        raise error.Abort(_("cannot specify both --noupdate and --updaterev"))

    r = hg.clone(ui, opts, source, dest,
                 pull=opts.get('pull'),
                 stream=opts.get('uncompressed'),
                 rev=opts.get('rev'),
                 update=opts.get('updaterev') or not opts.get('noupdate'),
                 branch=opts.get('branch'),
                 shareopts=opts.get('shareopts'))

    return r is None

@command('^commit|ci',
    [('A', 'addremove', None,
     _('mark new/missing files as added/removed before committing')),
    ('', 'close-branch', None,
     _('mark a branch head as closed')),
    ('', 'amend', None, _('amend the parent of the working directory')),
    ('s', 'secret', None, _('use the secret phase for committing')),
    ('e', 'edit', None, _('invoke editor on commit messages')),
    ('i', 'interactive', None, _('use interactive mode')),
    ] + walkopts + commitopts + commitopts2 + subrepoopts,
    _('[OPTION]... [FILE]...'),
    inferrepo=True)
def commit(ui, repo, *pats, **opts):
    """commit the specified files or all outstanding changes

    Commit changes to the given files into the repository. Unlike a
    centralized SCM, this operation is a local operation. See
    :hg:`push` for a way to actively distribute your changes.

    If a list of files is omitted, all changes reported by :hg:`status`
    will be committed.

    If you are committing the result of a merge, do not provide any
    filenames or -I/-X filters.

    If no commit message is specified, Mercurial starts your
    configured editor where you can enter a message. In case your
    commit fails, you will find a backup of your message in
    ``.hg/last-message.txt``.

    The --close-branch flag can be used to mark the current branch
    head closed. When all heads of a branch are closed, the branch
    will be considered closed and no longer listed.

    The --amend flag can be used to amend the parent of the
    working directory with a new commit that contains the changes
    in the parent in addition to those currently reported by :hg:`status`,
    if there are any. The old commit is stored in a backup bundle in
    ``.hg/strip-backup`` (see :hg:`help bundle` and :hg:`help unbundle`
    on how to restore it).

    Message, user and date are taken from the amended commit unless
    specified. When a message isn't specified on the command line,
    the editor will open with the message of the amended commit.

    It is not possible to amend public changesets (see :hg:`help phases`)
    or changesets that have children.

    See :hg:`help dates` for a list of formats valid for -d/--date.

    Returns 0 on success, 1 if nothing changed.

    .. container:: verbose

      Examples:

      - commit all files ending in .py::

          hg commit --include "set:**.py"

      - commit all non-binary files::

          hg commit --exclude "set:binary()"

      - amend the current commit and set the date to now::

          hg commit --amend --date now
    """
    wlock = lock = None
    try:
        wlock = repo.wlock()
        lock = repo.lock()
        return _docommit(ui, repo, *pats, **opts)
    finally:
        release(lock, wlock)

def _docommit(ui, repo, *pats, **opts):
    if opts.get('interactive'):
        opts.pop('interactive')
        ret = cmdutil.dorecord(ui, repo, commit, None, False,
                               cmdutil.recordfilter, *pats, **opts)
        # ret can be 0 (no changes to record) or the value returned by
        # commit(), 1 if nothing changed or None on success.
        return 1 if ret == 0 else ret

    if opts.get('subrepos'):
        if opts.get('amend'):
            raise error.Abort(_('cannot amend with --subrepos'))
        # Let --subrepos on the command line override config setting.
        ui.setconfig('ui', 'commitsubrepos', True, 'commit')

    cmdutil.checkunfinished(repo, commit=True)

    branch = repo[None].branch()
    bheads = repo.branchheads(branch)

    extra = {}
    if opts.get('close_branch'):
        extra['close'] = 1

        if not bheads:
            raise error.Abort(_('can only close branch heads'))
        elif opts.get('amend'):
            if repo[None].parents()[0].p1().branch() != branch and \
                    repo[None].parents()[0].p2().branch() != branch:
                raise error.Abort(_('can only close branch heads'))

    if opts.get('amend'):
        if ui.configbool('ui', 'commitsubrepos'):
            raise error.Abort(_('cannot amend with ui.commitsubrepos enabled'))

        old = repo['.']
        if not old.mutable():
            raise error.Abort(_('cannot amend public changesets'))
        if len(repo[None].parents()) > 1:
            raise error.Abort(_('cannot amend while merging'))
        allowunstable = obsolete.isenabled(repo, obsolete.allowunstableopt)
        if not allowunstable and old.children():
            raise error.Abort(_('cannot amend changeset with children'))

        # Currently histedit gets confused if an amend happens while histedit
        # is in progress. Since we have a checkunfinished command, we are
        # temporarily honoring it.
        #
        # Note: eventually this guard will be removed. Please do not expect
        # this behavior to remain.
        if not obsolete.isenabled(repo, obsolete.createmarkersopt):
            cmdutil.checkunfinished(repo)

        # commitfunc is used only for temporary amend commit by cmdutil.amend
        def commitfunc(ui, repo, message, match, opts):
            return repo.commit(message,
                               opts.get('user') or old.user(),
                               opts.get('date') or old.date(),
                               match,
                               extra=extra)

        node = cmdutil.amend(ui, repo, commitfunc, old, extra, pats, opts)
        if node == old.node():
            ui.status(_("nothing changed\n"))
            return 1
    else:
        def commitfunc(ui, repo, message, match, opts):
            backup = ui.backupconfig('phases', 'new-commit')
            baseui = repo.baseui
            basebackup = baseui.backupconfig('phases', 'new-commit')
            try:
                if opts.get('secret'):
                    ui.setconfig('phases', 'new-commit', 'secret', 'commit')
                    # Propagate to subrepos
                    baseui.setconfig('phases', 'new-commit', 'secret', 'commit')

                editform = cmdutil.mergeeditform(repo[None], 'commit.normal')
                editor = cmdutil.getcommiteditor(editform=editform, **opts)
                return repo.commit(message, opts.get('user'), opts.get('date'),
                                   match,
                                   editor=editor,
                                   extra=extra)
            finally:
                ui.restoreconfig(backup)
                repo.baseui.restoreconfig(basebackup)


        node = cmdutil.commit(ui, repo, commitfunc, pats, opts)

        if not node:
            stat = cmdutil.postcommitstatus(repo, pats, opts)
            if stat[3]:
                ui.status(_("nothing changed (%d missing files, see "
                            "'hg status')\n") % len(stat[3]))
            else:
                ui.status(_("nothing changed\n"))
            return 1

    cmdutil.commitstatus(repo, node, branch, bheads, opts)

@command('config|showconfig|debugconfig',
    [('u', 'untrusted', None, _('show untrusted configuration options')),
     ('e', 'edit', None, _('edit user config')),
     ('l', 'local', None, _('edit repository config')),
     ('g', 'global', None, _('edit global config'))] + formatteropts,
    _('[-u] [NAME]...'),
    optionalrepo=True)
def config(ui, repo, *values, **opts):
    """show combined config settings from all hgrc files

    With no arguments, print names and values of all config items.

    With one argument of the form section.name, print just the value
    of that config item.

    With multiple arguments, print names and values of all config
    items with matching section names.

    With --edit, start an editor on the user-level config file. With
    --global, edit the system-wide config file. With --local, edit the
    repository-level config file.

    With --debug, the source (filename and line number) is printed
    for each config item.

    See :hg:`help config` for more information about config files.

    Returns 0 on success, 1 if NAME does not exist.

    """

    if opts.get('edit') or opts.get('local') or opts.get('global'):
        if opts.get('local') and opts.get('global'):
            raise error.Abort(_("can't use --local and --global together"))

        if opts.get('local'):
            if not repo:
                raise error.Abort(_("can't use --local outside a repository"))
            paths = [repo.join('hgrc')]
        elif opts.get('global'):
            paths = scmutil.systemrcpath()
        else:
            paths = scmutil.userrcpath()

        for f in paths:
            if os.path.exists(f):
                break
        else:
            if opts.get('global'):
                samplehgrc = uimod.samplehgrcs['global']
            elif opts.get('local'):
                samplehgrc = uimod.samplehgrcs['local']
            else:
                samplehgrc = uimod.samplehgrcs['user']

            f = paths[0]
            fp = open(f, "w")
            fp.write(samplehgrc)
            fp.close()

        editor = ui.geteditor()
        ui.system("%s \"%s\"" % (editor, f),
                  onerr=error.Abort, errprefix=_("edit failed"))
        return

    fm = ui.formatter('config', opts)
    for f in scmutil.rcpath():
        ui.debug('read config from: %s\n' % f)
    untrusted = bool(opts.get('untrusted'))
    if values:
        sections = [v for v in values if '.' not in v]
        items = [v for v in values if '.' in v]
        if len(items) > 1 or items and sections:
            raise error.Abort(_('only one config item permitted'))
    matched = False
    for section, name, value in ui.walkconfig(untrusted=untrusted):
        value = str(value)
        if fm.isplain():
            value = value.replace('\n', '\\n')
        entryname = section + '.' + name
        if values:
            for v in values:
                if v == section:
                    fm.startitem()
                    fm.condwrite(ui.debugflag, 'source', '%s: ',
                                 ui.configsource(section, name, untrusted))
                    fm.write('name value', '%s=%s\n', entryname, value)
                    matched = True
                elif v == entryname:
                    fm.startitem()
                    fm.condwrite(ui.debugflag, 'source', '%s: ',
                                 ui.configsource(section, name, untrusted))
                    fm.write('value', '%s\n', value)
                    fm.data(name=entryname)
                    matched = True
        else:
            fm.startitem()
            fm.condwrite(ui.debugflag, 'source', '%s: ',
                         ui.configsource(section, name, untrusted))
            fm.write('name value', '%s=%s\n', entryname, value)
            matched = True
    fm.end()
    if matched:
        return 0
    return 1

@command('copy|cp',
    [('A', 'after', None, _('record a copy that has already occurred')),
    ('f', 'force', None, _('forcibly copy over an existing managed file')),
    ] + walkopts + dryrunopts,
    _('[OPTION]... [SOURCE]... DEST'))
def copy(ui, repo, *pats, **opts):
    """mark files as copied for the next commit

    Mark dest as having copies of source files. If dest is a
    directory, copies are put in that directory. If dest is a file,
    the source must be a single file.

    By default, this command copies the contents of files as they
    exist in the working directory. If invoked with -A/--after, the
    operation is recorded, but no copying is performed.

    This command takes effect with the next commit. To undo a copy
    before that, see :hg:`revert`.

    Returns 0 on success, 1 if errors are encountered.
    """
    with repo.wlock(False):
        return cmdutil.copy(ui, repo, pats, opts)

@command('debugancestor', [], _('[INDEX] REV1 REV2'), optionalrepo=True)
def debugancestor(ui, repo, *args):
    """find the ancestor revision of two revisions in a given index"""
    if len(args) == 3:
        index, rev1, rev2 = args
        r = revlog.revlog(scmutil.opener(os.getcwd(), audit=False), index)
        lookup = r.lookup
    elif len(args) == 2:
        if not repo:
            raise error.Abort(_("there is no Mercurial repository here "
                               "(.hg not found)"))
        rev1, rev2 = args
        r = repo.changelog
        lookup = repo.lookup
    else:
        raise error.Abort(_('either two or three arguments required'))
    a = r.ancestor(lookup(rev1), lookup(rev2))
    ui.write("%d:%s\n" % (r.rev(a), hex(a)))

@command('debugbuilddag',
    [('m', 'mergeable-file', None, _('add single file mergeable changes')),
    ('o', 'overwritten-file', None, _('add single file all revs overwrite')),
    ('n', 'new-file', None, _('add new file at each rev'))],
    _('[OPTION]... [TEXT]'))
def debugbuilddag(ui, repo, text=None,
                  mergeable_file=False,
                  overwritten_file=False,
                  new_file=False):
    """builds a repo with a given DAG from scratch in the current empty repo

    The description of the DAG is read from stdin if not given on the
    command line.

    Elements:

     - "+n" is a linear run of n nodes based on the current default parent
     - "." is a single node based on the current default parent
     - "$" resets the default parent to null (implied at the start);
           otherwise the default parent is always the last node created
     - "<p" sets the default parent to the backref p
     - "*p" is a fork at parent p, which is a backref
     - "*p1/p2" is a merge of parents p1 and p2, which are backrefs
     - "/p2" is a merge of the preceding node and p2
     - ":tag" defines a local tag for the preceding node
     - "@branch" sets the named branch for subsequent nodes
     - "#...\\n" is a comment up to the end of the line

    Whitespace between the above elements is ignored.

    A backref is either

     - a number n, which references the node curr-n, where curr is the current
       node, or
     - the name of a local tag you placed earlier using ":tag", or
     - empty to denote the default parent.

    All string valued-elements are either strictly alphanumeric, or must
    be enclosed in double quotes ("..."), with "\\" as escape character.
    """

    if text is None:
        ui.status(_("reading DAG from stdin\n"))
        text = ui.fin.read()

    cl = repo.changelog
    if len(cl) > 0:
        raise error.Abort(_('repository is not empty'))

    # determine number of revs in DAG
    total = 0
    for type, data in dagparser.parsedag(text):
        if type == 'n':
            total += 1

    if mergeable_file:
        linesperrev = 2
        # make a file with k lines per rev
        initialmergedlines = [str(i) for i in xrange(0, total * linesperrev)]
        initialmergedlines.append("")

    tags = []

    wlock = lock = tr = None
    try:
        wlock = repo.wlock()
        lock = repo.lock()
        tr = repo.transaction("builddag")

        at = -1
        atbranch = 'default'
        nodeids = []
        id = 0
        ui.progress(_('building'), id, unit=_('revisions'), total=total)
        for type, data in dagparser.parsedag(text):
            if type == 'n':
                ui.note(('node %s\n' % str(data)))
                id, ps = data

                files = []
                fctxs = {}

                p2 = None
                if mergeable_file:
                    fn = "mf"
                    p1 = repo[ps[0]]
                    if len(ps) > 1:
                        p2 = repo[ps[1]]
                        pa = p1.ancestor(p2)
                        base, local, other = [x[fn].data() for x in (pa, p1,
                                                                     p2)]
                        m3 = simplemerge.Merge3Text(base, local, other)
                        ml = [l.strip() for l in m3.merge_lines()]
                        ml.append("")
                    elif at > 0:
                        ml = p1[fn].data().split("\n")
                    else:
                        ml = initialmergedlines
                    ml[id * linesperrev] += " r%i" % id
                    mergedtext = "\n".join(ml)
                    files.append(fn)
                    fctxs[fn] = context.memfilectx(repo, fn, mergedtext)

                if overwritten_file:
                    fn = "of"
                    files.append(fn)
                    fctxs[fn] = context.memfilectx(repo, fn, "r%i\n" % id)

                if new_file:
                    fn = "nf%i" % id
                    files.append(fn)
                    fctxs[fn] = context.memfilectx(repo, fn, "r%i\n" % id)
                    if len(ps) > 1:
                        if not p2:
                            p2 = repo[ps[1]]
                        for fn in p2:
                            if fn.startswith("nf"):
                                files.append(fn)
                                fctxs[fn] = p2[fn]

                def fctxfn(repo, cx, path):
                    return fctxs.get(path)

                if len(ps) == 0 or ps[0] < 0:
                    pars = [None, None]
                elif len(ps) == 1:
                    pars = [nodeids[ps[0]], None]
                else:
                    pars = [nodeids[p] for p in ps]
                cx = context.memctx(repo, pars, "r%i" % id, files, fctxfn,
                                    date=(id, 0),
                                    user="debugbuilddag",
                                    extra={'branch': atbranch})
                nodeid = repo.commitctx(cx)
                nodeids.append(nodeid)
                at = id
            elif type == 'l':
                id, name = data
                ui.note(('tag %s\n' % name))
                tags.append("%s %s\n" % (hex(repo.changelog.node(id)), name))
            elif type == 'a':
                ui.note(('branch %s\n' % data))
                atbranch = data
            ui.progress(_('building'), id, unit=_('revisions'), total=total)
        tr.close()

        if tags:
            repo.vfs.write("localtags", "".join(tags))
    finally:
        ui.progress(_('building'), None)
        release(tr, lock, wlock)

@command('debugbundle',
        [('a', 'all', None, _('show all details')),
         ('', 'spec', None, _('print the bundlespec of the bundle'))],
        _('FILE'),
        norepo=True)
def debugbundle(ui, bundlepath, all=None, spec=None, **opts):
    """lists the contents of a bundle"""
    with hg.openpath(ui, bundlepath) as f:
        if spec:
            spec = exchange.getbundlespec(ui, f)
            ui.write('%s\n' % spec)
            return

        gen = exchange.readbundle(ui, f, bundlepath)
        if isinstance(gen, bundle2.unbundle20):
            return _debugbundle2(ui, gen, all=all, **opts)
        _debugchangegroup(ui, gen, all=all, **opts)

def _debugchangegroup(ui, gen, all=None, indent=0, **opts):
    indent_string = ' ' * indent
    if all:
        ui.write(("%sformat: id, p1, p2, cset, delta base, len(delta)\n")
                 % indent_string)

        def showchunks(named):
            ui.write("\n%s%s\n" % (indent_string, named))
            chain = None
            for chunkdata in iter(lambda: gen.deltachunk(chain), {}):
                node = chunkdata['node']
                p1 = chunkdata['p1']
                p2 = chunkdata['p2']
                cs = chunkdata['cs']
                deltabase = chunkdata['deltabase']
                delta = chunkdata['delta']
                ui.write("%s%s %s %s %s %s %s\n" %
                         (indent_string, hex(node), hex(p1), hex(p2),
                          hex(cs), hex(deltabase), len(delta)))
                chain = node

        chunkdata = gen.changelogheader()
        showchunks("changelog")
        chunkdata = gen.manifestheader()
        showchunks("manifest")
        for chunkdata in iter(gen.filelogheader, {}):
            fname = chunkdata['filename']
            showchunks(fname)
    else:
        if isinstance(gen, bundle2.unbundle20):
            raise error.Abort(_('use debugbundle2 for this file'))
        chunkdata = gen.changelogheader()
        chain = None
        for chunkdata in iter(lambda: gen.deltachunk(chain), {}):
            node = chunkdata['node']
            ui.write("%s%s\n" % (indent_string, hex(node)))
            chain = node

def _debugbundle2(ui, gen, all=None, **opts):
    """lists the contents of a bundle2"""
    if not isinstance(gen, bundle2.unbundle20):
        raise error.Abort(_('not a bundle2 file'))
    ui.write(('Stream params: %s\n' % repr(gen.params)))
    for part in gen.iterparts():
        ui.write('%s -- %r\n' % (part.type, repr(part.params)))
        if part.type == 'changegroup':
            version = part.params.get('version', '01')
            cg = changegroup.getunbundler(version, part, 'UN')
            _debugchangegroup(ui, cg, all=all, indent=4, **opts)

@command('debugcreatestreamclonebundle', [], 'FILE')
def debugcreatestreamclonebundle(ui, repo, fname):
    """create a stream clone bundle file

    Stream bundles are special bundles that are essentially archives of
    revlog files. They are commonly used for cloning very quickly.
    """
    requirements, gen = streamclone.generatebundlev1(repo)
    changegroup.writechunks(ui, gen, fname)

    ui.write(_('bundle requirements: %s\n') % ', '.join(sorted(requirements)))

@command('debugapplystreamclonebundle', [], 'FILE')
def debugapplystreamclonebundle(ui, repo, fname):
    """apply a stream clone bundle file"""
    f = hg.openpath(ui, fname)
    gen = exchange.readbundle(ui, f, fname)
    gen.apply(repo)

@command('debugcheckstate', [], '')
def debugcheckstate(ui, repo):
    """validate the correctness of the current dirstate"""
    parent1, parent2 = repo.dirstate.parents()
    m1 = repo[parent1].manifest()
    m2 = repo[parent2].manifest()
    errors = 0
    for f in repo.dirstate:
        state = repo.dirstate[f]
        if state in "nr" and f not in m1:
            ui.warn(_("%s in state %s, but not in manifest1\n") % (f, state))
            errors += 1
        if state in "a" and f in m1:
            ui.warn(_("%s in state %s, but also in manifest1\n") % (f, state))
            errors += 1
        if state in "m" and f not in m1 and f not in m2:
            ui.warn(_("%s in state %s, but not in either manifest\n") %
                    (f, state))
            errors += 1
    for f in m1:
        state = repo.dirstate[f]
        if state not in "nrm":
            ui.warn(_("%s in manifest1, but listed as state %s") % (f, state))
            errors += 1
    if errors:
        error = _(".hg/dirstate inconsistent with current parent's manifest")
        raise error.Abort(error)

@command('debugcommands', [], _('[COMMAND]'), norepo=True)
def debugcommands(ui, cmd='', *args):
    """list all available commands and options"""
    for cmd, vals in sorted(table.iteritems()):
        cmd = cmd.split('|')[0].strip('^')
        opts = ', '.join([i[1] for i in vals[1]])
        ui.write('%s: %s\n' % (cmd, opts))

@command('debugcomplete',
    [('o', 'options', None, _('show the command options'))],
    _('[-o] CMD'),
    norepo=True)
def debugcomplete(ui, cmd='', **opts):
    """returns the completion list associated with the given command"""

    if opts.get('options'):
        options = []
        otables = [globalopts]
        if cmd:
            aliases, entry = cmdutil.findcmd(cmd, table, False)
            otables.append(entry[1])
        for t in otables:
            for o in t:
                if "(DEPRECATED)" in o[3]:
                    continue
                if o[0]:
                    options.append('-%s' % o[0])
                options.append('--%s' % o[1])
        ui.write("%s\n" % "\n".join(options))
        return

    cmdlist, unused_allcmds = cmdutil.findpossible(cmd, table)
    if ui.verbose:
        cmdlist = [' '.join(c[0]) for c in cmdlist.values()]
    ui.write("%s\n" % "\n".join(sorted(cmdlist)))

@command('debugdag',
    [('t', 'tags', None, _('use tags as labels')),
    ('b', 'branches', None, _('annotate with branch names')),
    ('', 'dots', None, _('use dots for runs')),
    ('s', 'spaces', None, _('separate elements by spaces'))],
    _('[OPTION]... [FILE [REV]...]'),
    optionalrepo=True)
def debugdag(ui, repo, file_=None, *revs, **opts):
    """format the changelog or an index DAG as a concise textual description

    If you pass a revlog index, the revlog's DAG is emitted. If you list
    revision numbers, they get labeled in the output as rN.

    Otherwise, the changelog DAG of the current repo is emitted.
    """
    spaces = opts.get('spaces')
    dots = opts.get('dots')
    if file_:
        rlog = revlog.revlog(scmutil.opener(os.getcwd(), audit=False), file_)
        revs = set((int(r) for r in revs))
        def events():
            for r in rlog:
                yield 'n', (r, list(p for p in rlog.parentrevs(r)
                                        if p != -1))
                if r in revs:
                    yield 'l', (r, "r%i" % r)
    elif repo:
        cl = repo.changelog
        tags = opts.get('tags')
        branches = opts.get('branches')
        if tags:
            labels = {}
            for l, n in repo.tags().items():
                labels.setdefault(cl.rev(n), []).append(l)
        def events():
            b = "default"
            for r in cl:
                if branches:
                    newb = cl.read(cl.node(r))[5]['branch']
                    if newb != b:
                        yield 'a', newb
                        b = newb
                yield 'n', (r, list(p for p in cl.parentrevs(r)
                                        if p != -1))
                if tags:
                    ls = labels.get(r)
                    if ls:
                        for l in ls:
                            yield 'l', (r, l)
    else:
        raise error.Abort(_('need repo for changelog dag'))

    for line in dagparser.dagtextlines(events(),
                                       addspaces=spaces,
                                       wraplabels=True,
                                       wrapannotations=True,
                                       wrapnonlinear=dots,
                                       usedots=dots,
                                       maxlinewidth=70):
        ui.write(line)
        ui.write("\n")

@command('debugdata', debugrevlogopts, _('-c|-m|FILE REV'))
def debugdata(ui, repo, file_, rev=None, **opts):
    """dump the contents of a data file revision"""
    if opts.get('changelog') or opts.get('manifest') or opts.get('dir'):
        if rev is not None:
            raise error.CommandError('debugdata', _('invalid arguments'))
        file_, rev = None, file_
    elif rev is None:
        raise error.CommandError('debugdata', _('invalid arguments'))
    r = cmdutil.openrevlog(repo, 'debugdata', file_, opts)
    try:
        ui.write(r.revision(r.lookup(rev)))
    except KeyError:
        raise error.Abort(_('invalid revision identifier %s') % rev)

@command('debugdate',
    [('e', 'extended', None, _('try extended date formats'))],
    _('[-e] DATE [RANGE]'),
    norepo=True, optionalrepo=True)
def debugdate(ui, date, range=None, **opts):
    """parse and display a date"""
    if opts["extended"]:
        d = util.parsedate(date, util.extendeddateformats)
    else:
        d = util.parsedate(date)
    ui.write(("internal: %s %s\n") % d)
    ui.write(("standard: %s\n") % util.datestr(d))
    if range:
        m = util.matchdate(range)
        ui.write(("match: %s\n") % m(d[0]))

@command('debugdiscovery',
    [('', 'old', None, _('use old-style discovery')),
    ('', 'nonheads', None,
     _('use old-style discovery with non-heads included')),
    ] + remoteopts,
    _('[-l REV] [-r REV] [-b BRANCH]... [OTHER]'))
def debugdiscovery(ui, repo, remoteurl="default", **opts):
    """runs the changeset discovery protocol in isolation"""
    remoteurl, branches = hg.parseurl(ui.expandpath(remoteurl),
                                      opts.get('branch'))
    remote = hg.peer(repo, opts, remoteurl)
    ui.status(_('comparing with %s\n') % util.hidepassword(remoteurl))

    # make sure tests are repeatable
    random.seed(12323)

    def doit(localheads, remoteheads, remote=remote):
        if opts.get('old'):
            if localheads:
                raise error.Abort('cannot use localheads with old style '
                                 'discovery')
            if not util.safehasattr(remote, 'branches'):
                # enable in-client legacy support
                remote = localrepo.locallegacypeer(remote.local())
            common, _in, hds = treediscovery.findcommonincoming(repo, remote,
                                                                force=True)
            common = set(common)
            if not opts.get('nonheads'):
                ui.write(("unpruned common: %s\n") %
                         " ".join(sorted(short(n) for n in common)))
                dag = dagutil.revlogdag(repo.changelog)
                all = dag.ancestorset(dag.internalizeall(common))
                common = dag.externalizeall(dag.headsetofconnecteds(all))
        else:
            common, any, hds = setdiscovery.findcommonheads(ui, repo, remote)
        common = set(common)
        rheads = set(hds)
        lheads = set(repo.heads())
        ui.write(("common heads: %s\n") %
                 " ".join(sorted(short(n) for n in common)))
        if lheads <= common:
            ui.write(("local is subset\n"))
        elif rheads <= common:
            ui.write(("remote is subset\n"))

    serverlogs = opts.get('serverlog')
    if serverlogs:
        for filename in serverlogs:
            with open(filename, 'r') as logfile:
                line = logfile.readline()
                while line:
                    parts = line.strip().split(';')
                    op = parts[1]
                    if op == 'cg':
                        pass
                    elif op == 'cgss':
                        doit(parts[2].split(' '), parts[3].split(' '))
                    elif op == 'unb':
                        doit(parts[3].split(' '), parts[2].split(' '))
                    line = logfile.readline()
    else:
        remoterevs, _checkout = hg.addbranchrevs(repo, remote, branches,
                                                 opts.get('remote_head'))
        localrevs = opts.get('local_head')
        doit(localrevs, remoterevs)

@command('debugextensions', formatteropts, [], norepo=True)
def debugextensions(ui, **opts):
    '''show information about active extensions'''
    exts = extensions.extensions(ui)
    hgver = util.version()
    fm = ui.formatter('debugextensions', opts)
    for extname, extmod in sorted(exts, key=operator.itemgetter(0)):
        isinternal = extensions.ismoduleinternal(extmod)
        extsource = extmod.__file__
        if isinternal:
            exttestedwith = []  # never expose magic string to users
        else:
            exttestedwith = getattr(extmod, 'testedwith', '').split()
        extbuglink = getattr(extmod, 'buglink', None)

        fm.startitem()

        if ui.quiet or ui.verbose:
            fm.write('name', '%s\n', extname)
        else:
            fm.write('name', '%s', extname)
            if isinternal or hgver in exttestedwith:
                fm.plain('\n')
            elif not exttestedwith:
                fm.plain(_(' (untested!)\n'))
            else:
                lasttestedversion = exttestedwith[-1]
                fm.plain(' (%s!)\n' % lasttestedversion)

        fm.condwrite(ui.verbose and extsource, 'source',
                 _('  location: %s\n'), extsource or "")

        if ui.verbose:
            fm.plain(_('  bundled: %s\n') % ['no', 'yes'][isinternal])
        fm.data(bundled=isinternal)

        fm.condwrite(ui.verbose and exttestedwith, 'testedwith',
                     _('  tested with: %s\n'),
                     fm.formatlist(exttestedwith, name='ver'))

        fm.condwrite(ui.verbose and extbuglink, 'buglink',
                 _('  bug reporting: %s\n'), extbuglink or "")

    fm.end()

@command('debugfileset',
    [('r', 'rev', '', _('apply the filespec on this revision'), _('REV'))],
    _('[-r REV] FILESPEC'))
def debugfileset(ui, repo, expr, **opts):
    '''parse and apply a fileset specification'''
    ctx = scmutil.revsingle(repo, opts.get('rev'), None)
    if ui.verbose:
        tree = fileset.parse(expr)
        ui.note(fileset.prettyformat(tree), "\n")

    for f in ctx.getfileset(expr):
        ui.write("%s\n" % f)

@command('debugfsinfo', [], _('[PATH]'), norepo=True)
def debugfsinfo(ui, path="."):
    """show information detected about current filesystem"""
    util.writefile('.debugfsinfo', '')
    ui.write(('exec: %s\n') % (util.checkexec(path) and 'yes' or 'no'))
    ui.write(('symlink: %s\n') % (util.checklink(path) and 'yes' or 'no'))
    ui.write(('hardlink: %s\n') % (util.checknlink(path) and 'yes' or 'no'))
    ui.write(('case-sensitive: %s\n') % (util.fscasesensitive('.debugfsinfo')
                                and 'yes' or 'no'))
    os.unlink('.debugfsinfo')

@command('debuggetbundle',
    [('H', 'head', [], _('id of head node'), _('ID')),
    ('C', 'common', [], _('id of common node'), _('ID')),
    ('t', 'type', 'bzip2', _('bundle compression type to use'), _('TYPE'))],
    _('REPO FILE [-H|-C ID]...'),
    norepo=True)
def debuggetbundle(ui, repopath, bundlepath, head=None, common=None, **opts):
    """retrieves a bundle from a repo

    Every ID must be a full-length hex node id string. Saves the bundle to the
    given file.
    """
    repo = hg.peer(ui, opts, repopath)
    if not repo.capable('getbundle'):
        raise error.Abort("getbundle() not supported by target repository")
    args = {}
    if common:
        args['common'] = [bin(s) for s in common]
    if head:
        args['heads'] = [bin(s) for s in head]
    # TODO: get desired bundlecaps from command line.
    args['bundlecaps'] = None
    bundle = repo.getbundle('debug', **args)

    bundletype = opts.get('type', 'bzip2').lower()
    btypes = {'none': 'HG10UN',
              'bzip2': 'HG10BZ',
              'gzip': 'HG10GZ',
              'bundle2': 'HG20'}
    bundletype = btypes.get(bundletype)
    if bundletype not in bundle2.bundletypes:
        raise error.Abort(_('unknown bundle type specified with --type'))
    bundle2.writebundle(ui, bundle, bundlepath, bundletype)

@command('debugignore', [], '[FILE]')
def debugignore(ui, repo, *files, **opts):
    """display the combined ignore pattern and information about ignored files

    With no argument display the combined ignore pattern.

    Given space separated file names, shows if the given file is ignored and
    if so, show the ignore rule (file and line number) that matched it.
    """
    ignore = repo.dirstate._ignore
    if not files:
        # Show all the patterns
        includepat = getattr(ignore, 'includepat', None)
        if includepat is not None:
            ui.write("%s\n" % includepat)
        else:
            raise error.Abort(_("no ignore patterns found"))
    else:
        for f in files:
            nf = util.normpath(f)
            ignored = None
            ignoredata = None
            if nf != '.':
                if ignore(nf):
                    ignored = nf
                    ignoredata = repo.dirstate._ignorefileandline(nf)
                else:
                    for p in util.finddirs(nf):
                        if ignore(p):
                            ignored = p
                            ignoredata = repo.dirstate._ignorefileandline(p)
                            break
            if ignored:
                if ignored == nf:
                    ui.write(_("%s is ignored\n") % f)
                else:
                    ui.write(_("%s is ignored because of "
                               "containing folder %s\n")
                             % (f, ignored))
                ignorefile, lineno, line = ignoredata
                ui.write(_("(ignore rule in %s, line %d: '%s')\n")
                         % (ignorefile, lineno, line))
            else:
                ui.write(_("%s is not ignored\n") % f)

@command('debugindex', debugrevlogopts +
    [('f', 'format', 0, _('revlog format'), _('FORMAT'))],
    _('[-f FORMAT] -c|-m|FILE'),
    optionalrepo=True)
def debugindex(ui, repo, file_=None, **opts):
    """dump the contents of an index file"""
    r = cmdutil.openrevlog(repo, 'debugindex', file_, opts)
    format = opts.get('format', 0)
    if format not in (0, 1):
        raise error.Abort(_("unknown format %d") % format)

    generaldelta = r.version & revlog.REVLOGGENERALDELTA
    if generaldelta:
        basehdr = ' delta'
    else:
        basehdr = '  base'

    if ui.debugflag:
        shortfn = hex
    else:
        shortfn = short

    # There might not be anything in r, so have a sane default
    idlen = 12
    for i in r:
        idlen = len(shortfn(r.node(i)))
        break

    if format == 0:
        ui.write(("   rev    offset  length " + basehdr + " linkrev"
                 " %s %s p2\n") % ("nodeid".ljust(idlen), "p1".ljust(idlen)))
    elif format == 1:
        ui.write(("   rev flag   offset   length"
                 "     size " + basehdr + "   link     p1     p2"
                 " %s\n") % "nodeid".rjust(idlen))

    for i in r:
        node = r.node(i)
        if generaldelta:
            base = r.deltaparent(i)
        else:
            base = r.chainbase(i)
        if format == 0:
            try:
                pp = r.parents(node)
            except Exception:
                pp = [nullid, nullid]
            ui.write("% 6d % 9d % 7d % 6d % 7d %s %s %s\n" % (
                    i, r.start(i), r.length(i), base, r.linkrev(i),
                    shortfn(node), shortfn(pp[0]), shortfn(pp[1])))
        elif format == 1:
            pr = r.parentrevs(i)
            ui.write("% 6d %04x % 8d % 8d % 8d % 6d % 6d % 6d % 6d %s\n" % (
                    i, r.flags(i), r.start(i), r.length(i), r.rawsize(i),
                    base, r.linkrev(i), pr[0], pr[1], shortfn(node)))

@command('debugindexdot', debugrevlogopts,
    _('-c|-m|FILE'), optionalrepo=True)
def debugindexdot(ui, repo, file_=None, **opts):
    """dump an index DAG as a graphviz dot file"""
    r = cmdutil.openrevlog(repo, 'debugindexdot', file_, opts)
    ui.write(("digraph G {\n"))
    for i in r:
        node = r.node(i)
        pp = r.parents(node)
        ui.write("\t%d -> %d\n" % (r.rev(pp[0]), i))
        if pp[1] != nullid:
            ui.write("\t%d -> %d\n" % (r.rev(pp[1]), i))
    ui.write("}\n")

@command('debugdeltachain',
    debugrevlogopts + formatteropts,
    _('-c|-m|FILE'),
    optionalrepo=True)
def debugdeltachain(ui, repo, file_=None, **opts):
    """dump information about delta chains in a revlog

    Output can be templatized. Available template keywords are:

    :``rev``:       revision number
    :``chainid``:   delta chain identifier (numbered by unique base)
    :``chainlen``:  delta chain length to this revision
    :``prevrev``:   previous revision in delta chain
    :``deltatype``: role of delta / how it was computed
    :``compsize``:  compressed size of revision
    :``uncompsize``: uncompressed size of revision
    :``chainsize``: total size of compressed revisions in chain
    :``chainratio``: total chain size divided by uncompressed revision size
                    (new delta chains typically start at ratio 2.00)
    :``lindist``:   linear distance from base revision in delta chain to end
                    of this revision
    :``extradist``: total size of revisions not part of this delta chain from
                    base of delta chain to end of this revision; a measurement
                    of how much extra data we need to read/seek across to read
                    the delta chain for this revision
    :``extraratio``: extradist divided by chainsize; another representation of
                    how much unrelated data is needed to load this delta chain
    """
    r = cmdutil.openrevlog(repo, 'debugdeltachain', file_, opts)
    index = r.index
    generaldelta = r.version & revlog.REVLOGGENERALDELTA

    def revinfo(rev):
        e = index[rev]
        compsize = e[1]
        uncompsize = e[2]
        chainsize = 0

        if generaldelta:
            if e[3] == e[5]:
                deltatype = 'p1'
            elif e[3] == e[6]:
                deltatype = 'p2'
            elif e[3] == rev - 1:
                deltatype = 'prev'
            elif e[3] == rev:
                deltatype = 'base'
            else:
                deltatype = 'other'
        else:
            if e[3] == rev:
                deltatype = 'base'
            else:
                deltatype = 'prev'

        chain = r._deltachain(rev)[0]
        for iterrev in chain:
            e = index[iterrev]
            chainsize += e[1]

        return compsize, uncompsize, deltatype, chain, chainsize

    fm = ui.formatter('debugdeltachain', opts)

    fm.plain('    rev  chain# chainlen     prev   delta       '
             'size    rawsize  chainsize     ratio   lindist extradist '
             'extraratio\n')

    chainbases = {}
    for rev in r:
        comp, uncomp, deltatype, chain, chainsize = revinfo(rev)
        chainbase = chain[0]
        chainid = chainbases.setdefault(chainbase, len(chainbases) + 1)
        basestart = r.start(chainbase)
        revstart = r.start(rev)
        lineardist = revstart + comp - basestart
        extradist = lineardist - chainsize
        try:
            prevrev = chain[-2]
        except IndexError:
            prevrev = -1

        chainratio = float(chainsize) / float(uncomp)
        extraratio = float(extradist) / float(chainsize)

        fm.startitem()
        fm.write('rev chainid chainlen prevrev deltatype compsize '
                 'uncompsize chainsize chainratio lindist extradist '
                 'extraratio',
                 '%7d %7d %8d %8d %7s %10d %10d %10d %9.5f %9d %9d %10.5f\n',
                 rev, chainid, len(chain), prevrev, deltatype, comp,
                 uncomp, chainsize, chainratio, lineardist, extradist,
                 extraratio,
                 rev=rev, chainid=chainid, chainlen=len(chain),
                 prevrev=prevrev, deltatype=deltatype, compsize=comp,
                 uncompsize=uncomp, chainsize=chainsize,
                 chainratio=chainratio, lindist=lineardist,
                 extradist=extradist, extraratio=extraratio)

    fm.end()

@command('debuginstall', [] + formatteropts, '', norepo=True)
def debuginstall(ui, **opts):
    '''test Mercurial installation

    Returns 0 on success.
    '''

    def writetemp(contents):
        (fd, name) = tempfile.mkstemp(prefix="hg-debuginstall-")
        f = os.fdopen(fd, "wb")
        f.write(contents)
        f.close()
        return name

    problems = 0

    fm = ui.formatter('debuginstall', opts)
    fm.startitem()

    # encoding
    fm.write('encoding', _("checking encoding (%s)...\n"), encoding.encoding)
    err = None
    try:
        encoding.fromlocal("test")
    except error.Abort as inst:
        err = inst
        problems += 1
    fm.condwrite(err, 'encodingerror', _(" %s\n"
                 " (check that your locale is properly set)\n"), err)

    # Python
    fm.write('pythonexe', _("checking Python executable (%s)\n"),
             sys.executable)
    fm.write('pythonver', _("checking Python version (%s)\n"),
             ("%s.%s.%s" % sys.version_info[:3]))
    fm.write('pythonlib', _("checking Python lib (%s)...\n"),
             os.path.dirname(os.__file__))

    security = set(sslutil.supportedprotocols)
    if sslutil.hassni:
        security.add('sni')

    fm.write('pythonsecurity', _("checking Python security support (%s)\n"),
             fm.formatlist(sorted(security), name='protocol',
                           fmt='%s', sep=','))

    # These are warnings, not errors. So don't increment problem count. This
    # may change in the future.
    if 'tls1.2' not in security:
        fm.plain(_('  TLS 1.2 not supported by Python install; '
                   'network connections lack modern security\n'))
    if 'sni' not in security:
        fm.plain(_('  SNI not supported by Python install; may have '
                   'connectivity issues with some servers\n'))

    # TODO print CA cert info

    # hg version
    hgver = util.version()
    fm.write('hgver', _("checking Mercurial version (%s)\n"),
             hgver.split('+')[0])
    fm.write('hgverextra', _("checking Mercurial custom build (%s)\n"),
             '+'.join(hgver.split('+')[1:]))

    # compiled modules
    fm.write('hgmodulepolicy', _("checking module policy (%s)\n"),
             policy.policy)
    fm.write('hgmodules', _("checking installed modules (%s)...\n"),
             os.path.dirname(__file__))

    err = None
    try:
        from . import (
            base85,
            bdiff,
            mpatch,
            osutil,
        )
        dir(bdiff), dir(mpatch), dir(base85), dir(osutil) # quiet pyflakes
    except Exception as inst:
        err = inst
        problems += 1
    fm.condwrite(err, 'extensionserror', " %s\n", err)

    # templates
    p = templater.templatepaths()
    fm.write('templatedirs', 'checking templates (%s)...\n', ' '.join(p))
    fm.condwrite(not p, '', _(" no template directories found\n"))
    if p:
        m = templater.templatepath("map-cmdline.default")
        if m:
            # template found, check if it is working
            err = None
            try:
                templater.templater.frommapfile(m)
            except Exception as inst:
                err = inst
                p = None
            fm.condwrite(err, 'defaulttemplateerror', " %s\n", err)
        else:
            p = None
        fm.condwrite(p, 'defaulttemplate',
                     _("checking default template (%s)\n"), m)
        fm.condwrite(not m, 'defaulttemplatenotfound',
                     _(" template '%s' not found\n"), "default")
    if not p:
        problems += 1
    fm.condwrite(not p, '',
                 _(" (templates seem to have been installed incorrectly)\n"))

    # editor
    editor = ui.geteditor()
    editor = util.expandpath(editor)
    fm.write('editor', _("checking commit editor... (%s)\n"), editor)
    cmdpath = util.findexe(shlex.split(editor)[0])
    fm.condwrite(not cmdpath and editor == 'sensible-editor', 'vinotfound',
                 _(" No commit editor set and can't find %s in PATH\n"
                   " (specify a commit editor in your configuration"
                   " file)\n"), not cmdpath and editor == 'sensible-editor' and editor)
    fm.condwrite(not cmdpath and editor != 'sensible-editor', 'editornotfound',
                 _(" Can't find editor '%s' in PATH\n"
                   " (specify a commit editor in your configuration"
                   " file)\n"), not cmdpath and editor)
    if not cmdpath and editor != 'sensible-editor':
        problems += 1

    # check username
    username = None
    err = None
    try:
        username = ui.username()
    except error.Abort as e:
        err = e
        problems += 1

    fm.condwrite(username, 'username',  _("checking username (%s)\n"), username)
    fm.condwrite(err, 'usernameerror', _("checking username...\n %s\n"
        " (specify a username in your configuration file)\n"), err)

    fm.condwrite(not problems, '',
                 _("no problems detected\n"))
    if not problems:
        fm.data(problems=problems)
    fm.condwrite(problems, 'problems',
                 _("%d problems detected,"
                   " please check your install!\n"), problems)
    fm.end()

    return problems

@command('debugknown', [], _('REPO ID...'), norepo=True)
def debugknown(ui, repopath, *ids, **opts):
    """test whether node ids are known to a repo

    Every ID must be a full-length hex node id string. Returns a list of 0s
    and 1s indicating unknown/known.
    """
    repo = hg.peer(ui, opts, repopath)
    if not repo.capable('known'):
        raise error.Abort("known() not supported by target repository")
    flags = repo.known([bin(s) for s in ids])
    ui.write("%s\n" % ("".join([f and "1" or "0" for f in flags])))

@command('debuglabelcomplete', [], _('LABEL...'))
def debuglabelcomplete(ui, repo, *args):
    '''backwards compatibility with old bash completion scripts (DEPRECATED)'''
    debugnamecomplete(ui, repo, *args)

@command('debugmergestate', [], '')
def debugmergestate(ui, repo, *args):
    """print merge state

    Use --verbose to print out information about whether v1 or v2 merge state
    was chosen."""
    def _hashornull(h):
        if h == nullhex:
            return 'null'
        else:
            return h

    def printrecords(version):
        ui.write(('* version %s records\n') % version)
        if version == 1:
            records = v1records
        else:
            records = v2records

        for rtype, record in records:
            # pretty print some record types
            if rtype == 'L':
                ui.write(('local: %s\n') % record)
            elif rtype == 'O':
                ui.write(('other: %s\n') % record)
            elif rtype == 'm':
                driver, mdstate = record.split('\0', 1)
                ui.write(('merge driver: %s (state "%s")\n')
                         % (driver, mdstate))
            elif rtype in 'FDC':
                r = record.split('\0')
                f, state, hash, lfile, afile, anode, ofile = r[0:7]
                if version == 1:
                    onode = 'not stored in v1 format'
                    flags = r[7]
                else:
                    onode, flags = r[7:9]
                ui.write(('file: %s (record type "%s", state "%s", hash %s)\n')
                         % (f, rtype, state, _hashornull(hash)))
                ui.write(('  local path: %s (flags "%s")\n') % (lfile, flags))
                ui.write(('  ancestor path: %s (node %s)\n')
                         % (afile, _hashornull(anode)))
                ui.write(('  other path: %s (node %s)\n')
                         % (ofile, _hashornull(onode)))
            elif rtype == 'f':
                filename, rawextras = record.split('\0', 1)
                extras = rawextras.split('\0')
                i = 0
                extrastrings = []
                while i < len(extras):
                    extrastrings.append('%s = %s' % (extras[i], extras[i + 1]))
                    i += 2

                ui.write(('file extras: %s (%s)\n')
                         % (filename, ', '.join(extrastrings)))
            elif rtype == 'l':
                labels = record.split('\0', 2)
                labels = [l for l in labels if len(l) > 0]
                ui.write(('labels:\n'))
                ui.write(('  local: %s\n' % labels[0]))
                ui.write(('  other: %s\n' % labels[1]))
                if len(labels) > 2:
                    ui.write(('  base:  %s\n' % labels[2]))
            else:
                ui.write(('unrecognized entry: %s\t%s\n')
                         % (rtype, record.replace('\0', '\t')))

    # Avoid mergestate.read() since it may raise an exception for unsupported
    # merge state records. We shouldn't be doing this, but this is OK since this
    # command is pretty low-level.
    ms = mergemod.mergestate(repo)

    # sort so that reasonable information is on top
    v1records = ms._readrecordsv1()
    v2records = ms._readrecordsv2()
    order = 'LOml'
    def key(r):
        idx = order.find(r[0])
        if idx == -1:
            return (1, r[1])
        else:
            return (0, idx)
    v1records.sort(key=key)
    v2records.sort(key=key)

    if not v1records and not v2records:
        ui.write(('no merge state found\n'))
    elif not v2records:
        ui.note(('no version 2 merge state\n'))
        printrecords(1)
    elif ms._v1v2match(v1records, v2records):
        ui.note(('v1 and v2 states match: using v2\n'))
        printrecords(2)
    else:
        ui.note(('v1 and v2 states mismatch: using v1\n'))
        printrecords(1)
        if ui.verbose:
            printrecords(2)

@command('debugnamecomplete', [], _('NAME...'))
def debugnamecomplete(ui, repo, *args):
    '''complete "names" - tags, open branch names, bookmark names'''

    names = set()
    # since we previously only listed open branches, we will handle that
    # specially (after this for loop)
    for name, ns in repo.names.iteritems():
        if name != 'branches':
            names.update(ns.listnames(repo))
    names.update(tag for (tag, heads, tip, closed)
                 in repo.branchmap().iterbranches() if not closed)
    completions = set()
    if not args:
        args = ['']
    for a in args:
        completions.update(n for n in names if n.startswith(a))
    ui.write('\n'.join(sorted(completions)))
    ui.write('\n')

@command('debuglocks',
         [('L', 'force-lock', None, _('free the store lock (DANGEROUS)')),
          ('W', 'force-wlock', None,
           _('free the working state lock (DANGEROUS)'))],
         _('[OPTION]...'))
def debuglocks(ui, repo, **opts):
    """show or modify state of locks

    By default, this command will show which locks are held. This
    includes the user and process holding the lock, the amount of time
    the lock has been held, and the machine name where the process is
    running if it's not local.

    Locks protect the integrity of Mercurial's data, so should be
    treated with care. System crashes or other interruptions may cause
    locks to not be properly released, though Mercurial will usually
    detect and remove such stale locks automatically.

    However, detecting stale locks may not always be possible (for
    instance, on a shared filesystem). Removing locks may also be
    blocked by filesystem permissions.

    Returns 0 if no locks are held.

    """

    if opts.get('force_lock'):
        repo.svfs.unlink('lock')
    if opts.get('force_wlock'):
        repo.vfs.unlink('wlock')
    if opts.get('force_lock') or opts.get('force_lock'):
        return 0

    now = time.time()
    held = 0

    def report(vfs, name, method):
        # this causes stale locks to get reaped for more accurate reporting
        try:
            l = method(False)
        except error.LockHeld:
            l = None

        if l:
            l.release()
        else:
            try:
                stat = vfs.lstat(name)
                age = now - stat.st_mtime
                user = util.username(stat.st_uid)
                locker = vfs.readlock(name)
                if ":" in locker:
                    host, pid = locker.split(':')
                    if host == socket.gethostname():
                        locker = 'user %s, process %s' % (user, pid)
                    else:
                        locker = 'user %s, process %s, host %s' \
                                 % (user, pid, host)
                ui.write(("%-6s %s (%ds)\n") % (name + ":", locker, age))
                return 1
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise

        ui.write(("%-6s free\n") % (name + ":"))
        return 0

    held += report(repo.svfs, "lock", repo.lock)
    held += report(repo.vfs, "wlock", repo.wlock)

    return held

@command('debugobsolete',
        [('', 'flags', 0, _('markers flag')),
         ('', 'record-parents', False,
          _('record parent information for the precursor')),
         ('r', 'rev', [], _('display markers relevant to REV')),
         ('', 'index', False, _('display index of the marker')),
         ('', 'delete', [], _('delete markers specified by indices')),
        ] + commitopts2 + formatteropts,
         _('[OBSOLETED [REPLACEMENT ...]]'))
def debugobsolete(ui, repo, precursor=None, *successors, **opts):
    """create arbitrary obsolete marker

    With no arguments, displays the list of obsolescence markers."""

    def parsenodeid(s):
        try:
            # We do not use revsingle/revrange functions here to accept
            # arbitrary node identifiers, possibly not present in the
            # local repository.
            n = bin(s)
            if len(n) != len(nullid):
                raise TypeError()
            return n
        except TypeError:
            raise error.Abort('changeset references must be full hexadecimal '
                             'node identifiers')

    if opts.get('delete'):
        indices = []
        for v in opts.get('delete'):
            try:
                indices.append(int(v))
            except ValueError:
                raise error.Abort(_('invalid index value: %r') % v,
                                  hint=_('use integers for indices'))

        if repo.currenttransaction():
            raise error.Abort(_('cannot delete obsmarkers in the middle '
                                'of transaction.'))

        with repo.lock():
            n = repair.deleteobsmarkers(repo.obsstore, indices)
            ui.write(_('deleted %i obsolescense markers\n') % n)

        return

    if precursor is not None:
        if opts['rev']:
            raise error.Abort('cannot select revision when creating marker')
        metadata = {}
        metadata['user'] = opts['user'] or ui.username()
        succs = tuple(parsenodeid(succ) for succ in successors)
        l = repo.lock()
        try:
            tr = repo.transaction('debugobsolete')
            try:
                date = opts.get('date')
                if date:
                    date = util.parsedate(date)
                else:
                    date = None
                prec = parsenodeid(precursor)
                parents = None
                if opts['record_parents']:
                    if prec not in repo.unfiltered():
                        raise error.Abort('cannot used --record-parents on '
                                         'unknown changesets')
                    parents = repo.unfiltered()[prec].parents()
                    parents = tuple(p.node() for p in parents)
                repo.obsstore.create(tr, prec, succs, opts['flags'],
                                     parents=parents, date=date,
                                     metadata=metadata)
                tr.close()
            except ValueError as exc:
                raise error.Abort(_('bad obsmarker input: %s') % exc)
            finally:
                tr.release()
        finally:
            l.release()
    else:
        if opts['rev']:
            revs = scmutil.revrange(repo, opts['rev'])
            nodes = [repo[r].node() for r in revs]
            markers = list(obsolete.getmarkers(repo, nodes=nodes))
            markers.sort(key=lambda x: x._data)
        else:
            markers = obsolete.getmarkers(repo)

        markerstoiter = markers
        isrelevant = lambda m: True
        if opts.get('rev') and opts.get('index'):
            markerstoiter = obsolete.getmarkers(repo)
            markerset = set(markers)
            isrelevant = lambda m: m in markerset

        fm = ui.formatter('debugobsolete', opts)
        for i, m in enumerate(markerstoiter):
            if not isrelevant(m):
                # marker can be irrelevant when we're iterating over a set
                # of markers (markerstoiter) which is bigger than the set
                # of markers we want to display (markers)
                # this can happen if both --index and --rev options are
                # provided and thus we need to iterate over all of the markers
                # to get the correct indices, but only display the ones that
                # are relevant to --rev value
                continue
            fm.startitem()
            ind = i if opts.get('index') else None
            cmdutil.showmarker(fm, m, index=ind)
        fm.end()

@command('debugpathcomplete',
         [('f', 'full', None, _('complete an entire path')),
          ('n', 'normal', None, _('show only normal files')),
          ('a', 'added', None, _('show only added files')),
          ('r', 'removed', None, _('show only removed files'))],
         _('FILESPEC...'))
def debugpathcomplete(ui, repo, *specs, **opts):
    '''complete part or all of a tracked path

    This command supports shells that offer path name completion. It
    currently completes only files already known to the dirstate.

    Completion extends only to the next path segment unless
    --full is specified, in which case entire paths are used.'''

    def complete(path, acceptable):
        dirstate = repo.dirstate
        spec = os.path.normpath(os.path.join(os.getcwd(), path))
        rootdir = repo.root + os.sep
        if spec != repo.root and not spec.startswith(rootdir):
            return [], []
        if os.path.isdir(spec):
            spec += '/'
        spec = spec[len(rootdir):]
        fixpaths = os.sep != '/'
        if fixpaths:
            spec = spec.replace(os.sep, '/')
        speclen = len(spec)
        fullpaths = opts['full']
        files, dirs = set(), set()
        adddir, addfile = dirs.add, files.add
        for f, st in dirstate.iteritems():
            if f.startswith(spec) and st[0] in acceptable:
                if fixpaths:
                    f = f.replace('/', os.sep)
                if fullpaths:
                    addfile(f)
                    continue
                s = f.find(os.sep, speclen)
                if s >= 0:
                    adddir(f[:s])
                else:
                    addfile(f)
        return files, dirs

    acceptable = ''
    if opts['normal']:
        acceptable += 'nm'
    if opts['added']:
        acceptable += 'a'
    if opts['removed']:
        acceptable += 'r'
    cwd = repo.getcwd()
    if not specs:
        specs = ['.']

    files, dirs = set(), set()
    for spec in specs:
        f, d = complete(spec, acceptable or 'nmar')
        files.update(f)
        dirs.update(d)
    files.update(dirs)
    ui.write('\n'.join(repo.pathto(p, cwd) for p in sorted(files)))
    ui.write('\n')

@command('debugpushkey', [], _('REPO NAMESPACE [KEY OLD NEW]'), norepo=True)
def debugpushkey(ui, repopath, namespace, *keyinfo, **opts):
    '''access the pushkey key/value protocol

    With two args, list the keys in the given namespace.

    With five args, set a key to new if it currently is set to old.
    Reports success or failure.
    '''

    target = hg.peer(ui, {}, repopath)
    if keyinfo:
        key, old, new = keyinfo
        r = target.pushkey(namespace, key, old, new)
        ui.status(str(r) + '\n')
        return not r
    else:
        for k, v in sorted(target.listkeys(namespace).iteritems()):
            ui.write("%s\t%s\n" % (k.encode('string-escape'),
                                   v.encode('string-escape')))

@command('debugpvec', [], _('A B'))
def debugpvec(ui, repo, a, b=None):
    ca = scmutil.revsingle(repo, a)
    cb = scmutil.revsingle(repo, b)
    pa = pvec.ctxpvec(ca)
    pb = pvec.ctxpvec(cb)
    if pa == pb:
        rel = "="
    elif pa > pb:
        rel = ">"
    elif pa < pb:
        rel = "<"
    elif pa | pb:
        rel = "|"
    ui.write(_("a: %s\n") % pa)
    ui.write(_("b: %s\n") % pb)
    ui.write(_("depth(a): %d depth(b): %d\n") % (pa._depth, pb._depth))
    ui.write(_("delta: %d hdist: %d distance: %d relation: %s\n") %
             (abs(pa._depth - pb._depth), pvec._hamming(pa._vec, pb._vec),
              pa.distance(pb), rel))

@command('debugrebuilddirstate|debugrebuildstate',
    [('r', 'rev', '', _('revision to rebuild to'), _('REV')),
     ('', 'minimal', None, _('only rebuild files that are inconsistent with '
                             'the working copy parent')),
    ],
    _('[-r REV]'))
def debugrebuilddirstate(ui, repo, rev, **opts):
    """rebuild the dirstate as it would look like for the given revision

    If no revision is specified the first current parent will be used.

    The dirstate will be set to the files of the given revision.
    The actual working directory content or existing dirstate
    information such as adds or removes is not considered.

    ``minimal`` will only rebuild the dirstate status for files that claim to be
    tracked but are not in the parent manifest, or that exist in the parent
    manifest but are not in the dirstate. It will not change adds, removes, or
    modified files that are in the working copy parent.

    One use of this command is to make the next :hg:`status` invocation
    check the actual file content.
    """
    ctx = scmutil.revsingle(repo, rev)
    with repo.wlock():
        dirstate = repo.dirstate
        changedfiles = None
        # See command doc for what minimal does.
        if opts.get('minimal'):
            manifestfiles = set(ctx.manifest().keys())
            dirstatefiles = set(dirstate)
            manifestonly = manifestfiles - dirstatefiles
            dsonly = dirstatefiles - manifestfiles
            dsnotadded = set(f for f in dsonly if dirstate[f] != 'a')
            changedfiles = manifestonly | dsnotadded

        dirstate.rebuild(ctx.node(), ctx.manifest(), changedfiles)

@command('debugrebuildfncache', [], '')
def debugrebuildfncache(ui, repo):
    """rebuild the fncache file"""
    repair.rebuildfncache(ui, repo)

@command('debugrename',
    [('r', 'rev', '', _('revision to debug'), _('REV'))],
    _('[-r REV] FILE'))
def debugrename(ui, repo, file1, *pats, **opts):
    """dump rename information"""

    ctx = scmutil.revsingle(repo, opts.get('rev'))
    m = scmutil.match(ctx, (file1,) + pats, opts)
    for abs in ctx.walk(m):
        fctx = ctx[abs]
        o = fctx.filelog().renamed(fctx.filenode())
        rel = m.rel(abs)
        if o:
            ui.write(_("%s renamed from %s:%s\n") % (rel, o[0], hex(o[1])))
        else:
            ui.write(_("%s not renamed\n") % rel)

@command('debugrevlog', debugrevlogopts +
    [('d', 'dump', False, _('dump index data'))],
    _('-c|-m|FILE'),
    optionalrepo=True)
def debugrevlog(ui, repo, file_=None, **opts):
    """show data and statistics about a revlog"""
    r = cmdutil.openrevlog(repo, 'debugrevlog', file_, opts)

    if opts.get("dump"):
        numrevs = len(r)
        ui.write(("# rev p1rev p2rev start   end deltastart base   p1   p2"
                 " rawsize totalsize compression heads chainlen\n"))
        ts = 0
        heads = set()

        for rev in xrange(numrevs):
            dbase = r.deltaparent(rev)
            if dbase == -1:
                dbase = rev
            cbase = r.chainbase(rev)
            clen = r.chainlen(rev)
            p1, p2 = r.parentrevs(rev)
            rs = r.rawsize(rev)
            ts = ts + rs
            heads -= set(r.parentrevs(rev))
            heads.add(rev)
            try:
                compression = ts / r.end(rev)
            except ZeroDivisionError:
                compression = 0
            ui.write("%5d %5d %5d %5d %5d %10d %4d %4d %4d %7d %9d "
                     "%11d %5d %8d\n" %
                     (rev, p1, p2, r.start(rev), r.end(rev),
                      r.start(dbase), r.start(cbase),
                      r.start(p1), r.start(p2),
                      rs, ts, compression, len(heads), clen))
        return 0

    v = r.version
    format = v & 0xFFFF
    flags = []
    gdelta = False
    if v & revlog.REVLOGNGINLINEDATA:
        flags.append('inline')
    if v & revlog.REVLOGGENERALDELTA:
        gdelta = True
        flags.append('generaldelta')
    if not flags:
        flags = ['(none)']

    nummerges = 0
    numfull = 0
    numprev = 0
    nump1 = 0
    nump2 = 0
    numother = 0
    nump1prev = 0
    nump2prev = 0
    chainlengths = []

    datasize = [None, 0, 0]
    fullsize = [None, 0, 0]
    deltasize = [None, 0, 0]

    def addsize(size, l):
        if l[0] is None or size < l[0]:
            l[0] = size
        if size > l[1]:
            l[1] = size
        l[2] += size

    numrevs = len(r)
    for rev in xrange(numrevs):
        p1, p2 = r.parentrevs(rev)
        delta = r.deltaparent(rev)
        if format > 0:
            addsize(r.rawsize(rev), datasize)
        if p2 != nullrev:
            nummerges += 1
        size = r.length(rev)
        if delta == nullrev:
            chainlengths.append(0)
            numfull += 1
            addsize(size, fullsize)
        else:
            chainlengths.append(chainlengths[delta] + 1)
            addsize(size, deltasize)
            if delta == rev - 1:
                numprev += 1
                if delta == p1:
                    nump1prev += 1
                elif delta == p2:
                    nump2prev += 1
            elif delta == p1:
                nump1 += 1
            elif delta == p2:
                nump2 += 1
            elif delta != nullrev:
                numother += 1

    # Adjust size min value for empty cases
    for size in (datasize, fullsize, deltasize):
        if size[0] is None:
            size[0] = 0

    numdeltas = numrevs - numfull
    numoprev = numprev - nump1prev - nump2prev
    totalrawsize = datasize[2]
    datasize[2] /= numrevs
    fulltotal = fullsize[2]
    fullsize[2] /= numfull
    deltatotal = deltasize[2]
    if numrevs - numfull > 0:
        deltasize[2] /= numrevs - numfull
    totalsize = fulltotal + deltatotal
    avgchainlen = sum(chainlengths) / numrevs
    maxchainlen = max(chainlengths)
    compratio = 1
    if totalsize:
        compratio = totalrawsize / totalsize

    basedfmtstr = '%%%dd\n'
    basepcfmtstr = '%%%dd %s(%%5.2f%%%%)\n'

    def dfmtstr(max):
        return basedfmtstr % len(str(max))
    def pcfmtstr(max, padding=0):
        return basepcfmtstr % (len(str(max)), ' ' * padding)

    def pcfmt(value, total):
        if total:
            return (value, 100 * float(value) / total)
        else:
            return value, 100.0

    ui.write(('format : %d\n') % format)
    ui.write(('flags  : %s\n') % ', '.join(flags))

    ui.write('\n')
    fmt = pcfmtstr(totalsize)
    fmt2 = dfmtstr(totalsize)
    ui.write(('revisions     : ') + fmt2 % numrevs)
    ui.write(('    merges    : ') + fmt % pcfmt(nummerges, numrevs))
    ui.write(('    normal    : ') + fmt % pcfmt(numrevs - nummerges, numrevs))
    ui.write(('revisions     : ') + fmt2 % numrevs)
    ui.write(('    full      : ') + fmt % pcfmt(numfull, numrevs))
    ui.write(('    deltas    : ') + fmt % pcfmt(numdeltas, numrevs))
    ui.write(('revision size : ') + fmt2 % totalsize)
    ui.write(('    full      : ') + fmt % pcfmt(fulltotal, totalsize))
    ui.write(('    deltas    : ') + fmt % pcfmt(deltatotal, totalsize))

    ui.write('\n')
    fmt = dfmtstr(max(avgchainlen, compratio))
    ui.write(('avg chain length  : ') + fmt % avgchainlen)
    ui.write(('max chain length  : ') + fmt % maxchainlen)
    ui.write(('compression ratio : ') + fmt % compratio)

    if format > 0:
        ui.write('\n')
        ui.write(('uncompressed data size (min/max/avg) : %d / %d / %d\n')
                 % tuple(datasize))
    ui.write(('full revision size (min/max/avg)     : %d / %d / %d\n')
             % tuple(fullsize))
    ui.write(('delta size (min/max/avg)             : %d / %d / %d\n')
             % tuple(deltasize))

    if numdeltas > 0:
        ui.write('\n')
        fmt = pcfmtstr(numdeltas)
        fmt2 = pcfmtstr(numdeltas, 4)
        ui.write(('deltas against prev  : ') + fmt % pcfmt(numprev, numdeltas))
        if numprev > 0:
            ui.write(('    where prev = p1  : ') + fmt2 % pcfmt(nump1prev,
                                                              numprev))
            ui.write(('    where prev = p2  : ') + fmt2 % pcfmt(nump2prev,
                                                              numprev))
            ui.write(('    other            : ') + fmt2 % pcfmt(numoprev,
                                                              numprev))
        if gdelta:
            ui.write(('deltas against p1    : ')
                     + fmt % pcfmt(nump1, numdeltas))
            ui.write(('deltas against p2    : ')
                     + fmt % pcfmt(nump2, numdeltas))
            ui.write(('deltas against other : ') + fmt % pcfmt(numother,
                                                             numdeltas))

@command('debugrevspec',
    [('', 'optimize', None,
      _('print parsed tree after optimizing (DEPRECATED)')),
     ('p', 'show-stage', [],
      _('print parsed tree at the given stage'), _('NAME')),
     ('', 'no-optimized', False, _('evaluate tree without optimization')),
     ('', 'verify-optimized', False, _('verify optimized result')),
     ],
    ('REVSPEC'))
def debugrevspec(ui, repo, expr, **opts):
    """parse and apply a revision specification

    Use -p/--show-stage option to print the parsed tree at the given stages.
    Use -p all to print tree at every stage.

    Use --verify-optimized to compare the optimized result with the unoptimized
    one. Returns 1 if the optimized result differs.
    """
    stages = [
        ('parsed', lambda tree: tree),
        ('expanded', lambda tree: revset.expandaliases(ui, tree)),
        ('concatenated', revset.foldconcat),
        ('analyzed', revset.analyze),
        ('optimized', revset.optimize),
    ]
    if opts['no_optimized']:
        stages = stages[:-1]
    if opts['verify_optimized'] and opts['no_optimized']:
        raise error.Abort(_('cannot use --verify-optimized with '
                            '--no-optimized'))
    stagenames = set(n for n, f in stages)

    showalways = set()
    showchanged = set()
    if ui.verbose and not opts['show_stage']:
        # show parsed tree by --verbose (deprecated)
        showalways.add('parsed')
        showchanged.update(['expanded', 'concatenated'])
        if opts['optimize']:
            showalways.add('optimized')
    if opts['show_stage'] and opts['optimize']:
        raise error.Abort(_('cannot use --optimize with --show-stage'))
    if opts['show_stage'] == ['all']:
        showalways.update(stagenames)
    else:
        for n in opts['show_stage']:
            if n not in stagenames:
                raise error.Abort(_('invalid stage name: %s') % n)
        showalways.update(opts['show_stage'])

    treebystage = {}
    printedtree = None
    tree = revset.parse(expr, lookup=repo.__contains__)
    for n, f in stages:
        treebystage[n] = tree = f(tree)
        if n in showalways or (n in showchanged and tree != printedtree):
            if opts['show_stage'] or n != 'parsed':
                ui.write(("* %s:\n") % n)
            ui.write(revset.prettyformat(tree), "\n")
            printedtree = tree

    if opts['verify_optimized']:
        arevs = revset.makematcher(treebystage['analyzed'])(repo)
        brevs = revset.makematcher(treebystage['optimized'])(repo)
        if ui.verbose:
            ui.note(("* analyzed set:\n"), revset.prettyformatset(arevs), "\n")
            ui.note(("* optimized set:\n"), revset.prettyformatset(brevs), "\n")
        arevs = list(arevs)
        brevs = list(brevs)
        if arevs == brevs:
            return 0
        ui.write(('--- analyzed\n'), label='diff.file_a')
        ui.write(('+++ optimized\n'), label='diff.file_b')
        sm = difflib.SequenceMatcher(None, arevs, brevs)
        for tag, alo, ahi, blo, bhi in sm.get_opcodes():
            if tag in ('delete', 'replace'):
                for c in arevs[alo:ahi]:
                    ui.write('-%s\n' % c, label='diff.deleted')
            if tag in ('insert', 'replace'):
                for c in brevs[blo:bhi]:
                    ui.write('+%s\n' % c, label='diff.inserted')
            if tag == 'equal':
                for c in arevs[alo:ahi]:
                    ui.write(' %s\n' % c)
        return 1

    func = revset.makematcher(tree)
    revs = func(repo)
    if ui.verbose:
        ui.note(("* set:\n"), revset.prettyformatset(revs), "\n")
    for c in revs:
        ui.write("%s\n" % c)

@command('debugsetparents', [], _('REV1 [REV2]'))
def debugsetparents(ui, repo, rev1, rev2=None):
    """manually set the parents of the current working directory

    This is useful for writing repository conversion tools, but should
    be used with care. For example, neither the working directory nor the
    dirstate is updated, so file status may be incorrect after running this
    command.

    Returns 0 on success.
    """

    r1 = scmutil.revsingle(repo, rev1).node()
    r2 = scmutil.revsingle(repo, rev2, 'null').node()

    with repo.wlock():
        repo.setparents(r1, r2)

@command('debugdirstate|debugstate',
    [('', 'nodates', None, _('do not display the saved mtime')),
    ('', 'datesort', None, _('sort by saved mtime'))],
    _('[OPTION]...'))
def debugstate(ui, repo, **opts):
    """show the contents of the current dirstate"""

    nodates = opts.get('nodates')
    datesort = opts.get('datesort')

    timestr = ""
    if datesort:
        keyfunc = lambda x: (x[1][3], x[0]) # sort by mtime, then by filename
    else:
        keyfunc = None # sort by filename
    for file_, ent in sorted(repo.dirstate._map.iteritems(), key=keyfunc):
        if ent[3] == -1:
            timestr = 'unset               '
        elif nodates:
            timestr = 'set                 '
        else:
            timestr = time.strftime("%Y-%m-%d %H:%M:%S ",
                                    time.localtime(ent[3]))
        if ent[1] & 0o20000:
            mode = 'lnk'
        else:
            mode = '%3o' % (ent[1] & 0o777 & ~util.umask)
        ui.write("%c %s %10d %s%s\n" % (ent[0], mode, ent[2], timestr, file_))
    for f in repo.dirstate.copies():
        ui.write(_("copy: %s -> %s\n") % (repo.dirstate.copied(f), f))

@command('debugsub',
    [('r', 'rev', '',
     _('revision to check'), _('REV'))],
    _('[-r REV] [REV]'))
def debugsub(ui, repo, rev=None):
    ctx = scmutil.revsingle(repo, rev, None)
    for k, v in sorted(ctx.substate.items()):
        ui.write(('path %s\n') % k)
        ui.write((' source   %s\n') % v[0])
        ui.write((' revision %s\n') % v[1])

@command('debugsuccessorssets',
    [],
    _('[REV]'))
def debugsuccessorssets(ui, repo, *revs):
    """show set of successors for revision

    A successors set of changeset A is a consistent group of revisions that
    succeed A. It contains non-obsolete changesets only.

    In most cases a changeset A has a single successors set containing a single
    successor (changeset A replaced by A').

    A changeset that is made obsolete with no successors are called "pruned".
    Such changesets have no successors sets at all.

    A changeset that has been "split" will have a successors set containing
    more than one successor.

    A changeset that has been rewritten in multiple different ways is called
    "divergent". Such changesets have multiple successor sets (each of which
    may also be split, i.e. have multiple successors).

    Results are displayed as follows::

        <rev1>
            <successors-1A>
        <rev2>
            <successors-2A>
            <successors-2B1> <successors-2B2> <successors-2B3>

    Here rev2 has two possible (i.e. divergent) successors sets. The first
    holds one element, whereas the second holds three (i.e. the changeset has
    been split).
    """
    # passed to successorssets caching computation from one call to another
    cache = {}
    ctx2str = str
    node2str = short
    if ui.debug():
        def ctx2str(ctx):
            return ctx.hex()
        node2str = hex
    for rev in scmutil.revrange(repo, revs):
        ctx = repo[rev]
        ui.write('%s\n'% ctx2str(ctx))
        for succsset in obsolete.successorssets(repo, ctx.node(), cache):
            if succsset:
                ui.write('    ')
                ui.write(node2str(succsset[0]))
                for node in succsset[1:]:
                    ui.write(' ')
                    ui.write(node2str(node))
            ui.write('\n')

@command('debugtemplate',
    [('r', 'rev', [], _('apply template on changesets'), _('REV')),
     ('D', 'define', [], _('define template keyword'), _('KEY=VALUE'))],
    _('[-r REV]... [-D KEY=VALUE]... TEMPLATE'),
    optionalrepo=True)
def debugtemplate(ui, repo, tmpl, **opts):
    """parse and apply a template

    If -r/--rev is given, the template is processed as a log template and
    applied to the given changesets. Otherwise, it is processed as a generic
    template.

    Use --verbose to print the parsed tree.
    """
    revs = None
    if opts['rev']:
        if repo is None:
            raise error.RepoError(_('there is no Mercurial repository here '
                                    '(.hg not found)'))
        revs = scmutil.revrange(repo, opts['rev'])

    props = {}
    for d in opts['define']:
        try:
            k, v = (e.strip() for e in d.split('=', 1))
            if not k:
                raise ValueError
            props[k] = v
        except ValueError:
            raise error.Abort(_('malformed keyword definition: %s') % d)

    if ui.verbose:
        aliases = ui.configitems('templatealias')
        tree = templater.parse(tmpl)
        ui.note(templater.prettyformat(tree), '\n')
        newtree = templater.expandaliases(tree, aliases)
        if newtree != tree:
            ui.note(("* expanded:\n"), templater.prettyformat(newtree), '\n')

    mapfile = None
    if revs is None:
        k = 'debugtemplate'
        t = formatter.maketemplater(ui, k, tmpl)
        ui.write(templater.stringify(t(k, **props)))
    else:
        displayer = cmdutil.changeset_templater(ui, repo, None, opts, tmpl,
                                                mapfile, buffered=False)
        for r in revs:
            displayer.show(repo[r], **props)
        displayer.close()

@command('debugwalk', walkopts, _('[OPTION]... [FILE]...'), inferrepo=True)
def debugwalk(ui, repo, *pats, **opts):
    """show how files match on given patterns"""
    m = scmutil.match(repo[None], pats, opts)
    items = list(repo.walk(m))
    if not items:
        return
    f = lambda fn: fn
    if ui.configbool('ui', 'slash') and os.sep != '/':
        f = lambda fn: util.normpath(fn)
    fmt = 'f  %%-%ds  %%-%ds  %%s' % (
        max([len(abs) for abs in items]),
        max([len(m.rel(abs)) for abs in items]))
    for abs in items:
        line = fmt % (abs, f(m.rel(abs)), m.exact(abs) and 'exact' or '')
        ui.write("%s\n" % line.rstrip())

@command('debugwireargs',
    [('', 'three', '', 'three'),
    ('', 'four', '', 'four'),
    ('', 'five', '', 'five'),
    ] + remoteopts,
    _('REPO [OPTIONS]... [ONE [TWO]]'),
    norepo=True)
def debugwireargs(ui, repopath, *vals, **opts):
    repo = hg.peer(ui, opts, repopath)
    for opt in remoteopts:
        del opts[opt[1]]
    args = {}
    for k, v in opts.iteritems():
        if v:
            args[k] = v
    # run twice to check that we don't mess up the stream for the next command
    res1 = repo.debugwireargs(*vals, **args)
    res2 = repo.debugwireargs(*vals, **args)
    ui.write("%s\n" % res1)
    if res1 != res2:
        ui.warn("%s\n" % res2)

@command('^diff',
    [('r', 'rev', [], _('revision'), _('REV')),
    ('c', 'change', '', _('change made by revision'), _('REV'))
    ] + diffopts + diffopts2 + walkopts + subrepoopts,
    _('[OPTION]... ([-c REV] | [-r REV1 [-r REV2]]) [FILE]...'),
    inferrepo=True)
def diff(ui, repo, *pats, **opts):
    """diff repository (or selected files)

    Show differences between revisions for the specified files.

    Differences between files are shown using the unified diff format.

    .. note::

       :hg:`diff` may generate unexpected results for merges, as it will
       default to comparing against the working directory's first
       parent changeset if no revisions are specified.

    When two revision arguments are given, then changes are shown
    between those revisions. If only one revision is specified then
    that revision is compared to the working directory, and, when no
    revisions are specified, the working directory files are compared
    to its first parent.

    Alternatively you can specify -c/--change with a revision to see
    the changes in that changeset relative to its first parent.

    Without the -a/--text option, diff will avoid generating diffs of
    files it detects as binary. With -a, diff will generate a diff
    anyway, probably with undesirable results.

    Use the -g/--git option to generate diffs in the git extended diff
    format. For more information, read :hg:`help diffs`.

    .. container:: verbose

      Examples:

      - compare a file in the current working directory to its parent::

          hg diff foo.c

      - compare two historical versions of a directory, with rename info::

          hg diff --git -r 1.0:1.2 lib/

      - get change stats relative to the last change on some date::

          hg diff --stat -r "date('may 2')"

      - diff all newly-added files that contain a keyword::

          hg diff "set:added() and grep(GNU)"

      - compare a revision and its parents::

          hg diff -c 9353         # compare against first parent
          hg diff -r 9353^:9353   # same using revset syntax
          hg diff -r 9353^2:9353  # compare against the second parent

    Returns 0 on success.
    """

    revs = opts.get('rev')
    change = opts.get('change')
    stat = opts.get('stat')
    reverse = opts.get('reverse')

    if revs and change:
        msg = _('cannot specify --rev and --change at the same time')
        raise error.Abort(msg)
    elif change:
        node2 = scmutil.revsingle(repo, change, None).node()
        node1 = repo[node2].p1().node()
    else:
        node1, node2 = scmutil.revpair(repo, revs)

    if reverse:
        node1, node2 = node2, node1

    diffopts = patch.diffallopts(ui, opts)
    m = scmutil.match(repo[node2], pats, opts)
    cmdutil.diffordiffstat(ui, repo, diffopts, node1, node2, m, stat=stat,
                           listsubrepos=opts.get('subrepos'),
                           root=opts.get('root'))

@command('^export',
    [('o', 'output', '',
     _('print output to file with formatted name'), _('FORMAT')),
    ('', 'switch-parent', None, _('diff against the second parent')),
    ('r', 'rev', [], _('revisions to export'), _('REV')),
    ] + diffopts,
    _('[OPTION]... [-o OUTFILESPEC] [-r] [REV]...'))
def export(ui, repo, *changesets, **opts):
    """dump the header and diffs for one or more changesets

    Print the changeset header and diffs for one or more revisions.
    If no revision is given, the parent of the working directory is used.

    The information shown in the changeset header is: author, date,
    branch name (if non-default), changeset hash, parent(s) and commit
    comment.

    .. note::

       :hg:`export` may generate unexpected diff output for merge
       changesets, as it will compare the merge changeset against its
       first parent only.

    Output may be to a file, in which case the name of the file is
    given using a format string. The formatting rules are as follows:

    :``%%``: literal "%" character
    :``%H``: changeset hash (40 hexadecimal digits)
    :``%N``: number of patches being generated
    :``%R``: changeset revision number
    :``%b``: basename of the exporting repository
    :``%h``: short-form changeset hash (12 hexadecimal digits)
    :``%m``: first line of the commit message (only alphanumeric characters)
    :``%n``: zero-padded sequence number, starting at 1
    :``%r``: zero-padded changeset revision number

    Without the -a/--text option, export will avoid generating diffs
    of files it detects as binary. With -a, export will generate a
    diff anyway, probably with undesirable results.

    Use the -g/--git option to generate diffs in the git extended diff
    format. See :hg:`help diffs` for more information.

    With the --switch-parent option, the diff will be against the
    second parent. It can be useful to review a merge.

    .. container:: verbose

      Examples:

      - use export and import to transplant a bugfix to the current
        branch::

          hg export -r 9353 | hg import -

      - export all the changesets between two revisions to a file with
        rename information::

          hg export --git -r 123:150 > changes.txt

      - split outgoing changes into a series of patches with
        descriptive names::

          hg export -r "outgoing()" -o "%n-%m.patch"

    Returns 0 on success.
    """
    changesets += tuple(opts.get('rev', []))
    if not changesets:
        changesets = ['.']
    revs = scmutil.revrange(repo, changesets)
    if not revs:
        raise error.Abort(_("export requires at least one changeset"))
    if len(revs) > 1:
        ui.note(_('exporting patches:\n'))
    else:
        ui.note(_('exporting patch:\n'))
    cmdutil.export(repo, revs, template=opts.get('output'),
                 switch_parent=opts.get('switch_parent'),
                 opts=patch.diffallopts(ui, opts))

@command('files',
    [('r', 'rev', '', _('search the repository as it is in REV'), _('REV')),
     ('0', 'print0', None, _('end filenames with NUL, for use with xargs')),
    ] + walkopts + formatteropts + subrepoopts,
    _('[OPTION]... [FILE]...'))
def files(ui, repo, *pats, **opts):
    """list tracked files

    Print files under Mercurial control in the working directory or
    specified revision for given files (excluding removed files).
    Files can be specified as filenames or filesets.

    If no files are given to match, this command prints the names
    of all files under Mercurial control.

    .. container:: verbose

      Examples:

      - list all files under the current directory::

          hg files .

      - shows sizes and flags for current revision::

          hg files -vr .

      - list all files named README::

          hg files -I "**/README"

      - list all binary files::

          hg files "set:binary()"

      - find files containing a regular expression::

          hg files "set:grep('bob')"

      - search tracked file contents with xargs and grep::

          hg files -0 | xargs -0 grep foo

    See :hg:`help patterns` and :hg:`help filesets` for more information
    on specifying file patterns.

    Returns 0 if a match is found, 1 otherwise.

    """
    ctx = scmutil.revsingle(repo, opts.get('rev'), None)

    end = '\n'
    if opts.get('print0'):
        end = '\0'
    fmt = '%s' + end

    m = scmutil.match(ctx, pats, opts)
    with ui.formatter('files', opts) as fm:
        return cmdutil.files(ui, ctx, m, fm, fmt, opts.get('subrepos'))

@command('^forget', walkopts, _('[OPTION]... FILE...'), inferrepo=True)
def forget(ui, repo, *pats, **opts):
    """forget the specified files on the next commit

    Mark the specified files so they will no longer be tracked
    after the next commit.

    This only removes files from the current branch, not from the
    entire project history, and it does not delete them from the
    working directory.

    To delete the file from the working directory, see :hg:`remove`.

    To undo a forget before the next commit, see :hg:`add`.

    .. container:: verbose

      Examples:

      - forget newly-added binary files::

          hg forget "set:added() and binary()"

      - forget files that would be excluded by .hgignore::

          hg forget "set:hgignore()"

    Returns 0 on success.
    """

    if not pats:
        raise error.Abort(_('no files specified'))

    m = scmutil.match(repo[None], pats, opts)
    rejected = cmdutil.forget(ui, repo, m, prefix="", explicitonly=False)[0]
    return rejected and 1 or 0

@command(
    'graft',
    [('r', 'rev', [], _('revisions to graft'), _('REV')),
     ('c', 'continue', False, _('resume interrupted graft')),
     ('e', 'edit', False, _('invoke editor on commit messages')),
     ('', 'log', None, _('append graft info to log message')),
     ('f', 'force', False, _('force graft')),
     ('D', 'currentdate', False,
      _('record the current date as commit date')),
     ('U', 'currentuser', False,
      _('record the current user as committer'), _('DATE'))]
    + commitopts2 + mergetoolopts  + dryrunopts,
    _('[OPTION]... [-r REV]... REV...'))
def graft(ui, repo, *revs, **opts):
    '''copy changes from other branches onto the current branch

    This command uses Mercurial's merge logic to copy individual
    changes from other branches without merging branches in the
    history graph. This is sometimes known as 'backporting' or
    'cherry-picking'. By default, graft will copy user, date, and
    description from the source changesets.

    Changesets that are ancestors of the current revision, that have
    already been grafted, or that are merges will be skipped.

    If --log is specified, log messages will have a comment appended
    of the form::

      (grafted from CHANGESETHASH)

    If --force is specified, revisions will be grafted even if they
    are already ancestors of or have been grafted to the destination.
    This is useful when the revisions have since been backed out.

    If a graft merge results in conflicts, the graft process is
    interrupted so that the current merge can be manually resolved.
    Once all conflicts are addressed, the graft process can be
    continued with the -c/--continue option.

    .. note::

       The -c/--continue option does not reapply earlier options, except
       for --force.

    .. container:: verbose

      Examples:

      - copy a single change to the stable branch and edit its description::

          hg update stable
          hg graft --edit 9393

      - graft a range of changesets with one exception, updating dates::

          hg graft -D "2085::2093 and not 2091"

      - continue a graft after resolving conflicts::

          hg graft -c

      - show the source of a grafted changeset::

          hg log --debug -r .

      - show revisions sorted by date::

          hg log -r "sort(all(), date)"

    See :hg:`help revisions` and :hg:`help revsets` for more about
    specifying revisions.

    Returns 0 on successful completion.
    '''
    with repo.wlock():
        return _dograft(ui, repo, *revs, **opts)

def _dograft(ui, repo, *revs, **opts):
    if revs and opts.get('rev'):
        ui.warn(_('warning: inconsistent use of --rev might give unexpected '
                  'revision ordering!\n'))

    revs = list(revs)
    revs.extend(opts.get('rev'))

    if not opts.get('user') and opts.get('currentuser'):
        opts['user'] = ui.username()
    if not opts.get('date') and opts.get('currentdate'):
        opts['date'] = "%d %d" % util.makedate()

    editor = cmdutil.getcommiteditor(editform='graft', **opts)

    cont = False
    if opts.get('continue'):
        cont = True
        if revs:
            raise error.Abort(_("can't specify --continue and revisions"))
        # read in unfinished revisions
        try:
            nodes = repo.vfs.read('graftstate').splitlines()
            revs = [repo[node].rev() for node in nodes]
        except IOError as inst:
            if inst.errno != errno.ENOENT:
                raise
            cmdutil.wrongtooltocontinue(repo, _('graft'))
    else:
        cmdutil.checkunfinished(repo)
        cmdutil.bailifchanged(repo)
        if not revs:
            raise error.Abort(_('no revisions specified'))
        revs = scmutil.revrange(repo, revs)

    skipped = set()
    # check for merges
    for rev in repo.revs('%ld and merge()', revs):
        ui.warn(_('skipping ungraftable merge revision %s\n') % rev)
        skipped.add(rev)
    revs = [r for r in revs if r not in skipped]
    if not revs:
        return -1

    # Don't check in the --continue case, in effect retaining --force across
    # --continues. That's because without --force, any revisions we decided to
    # skip would have been filtered out here, so they wouldn't have made their
    # way to the graftstate. With --force, any revisions we would have otherwise
    # skipped would not have been filtered out, and if they hadn't been applied
    # already, they'd have been in the graftstate.
    if not (cont or opts.get('force')):
        # check for ancestors of dest branch
        crev = repo['.'].rev()
        ancestors = repo.changelog.ancestors([crev], inclusive=True)
        # XXX make this lazy in the future
        # don't mutate while iterating, create a copy
        for rev in list(revs):
            if rev in ancestors:
                ui.warn(_('skipping ancestor revision %d:%s\n') %
                        (rev, repo[rev]))
                # XXX remove on list is slow
                revs.remove(rev)
        if not revs:
            return -1

        # analyze revs for earlier grafts
        ids = {}
        for ctx in repo.set("%ld", revs):
            ids[ctx.hex()] = ctx.rev()
            n = ctx.extra().get('source')
            if n:
                ids[n] = ctx.rev()

        # check ancestors for earlier grafts
        ui.debug('scanning for duplicate grafts\n')

        for rev in repo.changelog.findmissingrevs(revs, [crev]):
            ctx = repo[rev]
            n = ctx.extra().get('source')
            if n in ids:
                try:
                    r = repo[n].rev()
                except error.RepoLookupError:
                    r = None
                if r in revs:
                    ui.warn(_('skipping revision %d:%s '
                              '(already grafted to %d:%s)\n')
                            % (r, repo[r], rev, ctx))
                    revs.remove(r)
                elif ids[n] in revs:
                    if r is None:
                        ui.warn(_('skipping already grafted revision %d:%s '
                                  '(%d:%s also has unknown origin %s)\n')
                                % (ids[n], repo[ids[n]], rev, ctx, n[:12]))
                    else:
                        ui.warn(_('skipping already grafted revision %d:%s '
                                  '(%d:%s also has origin %d:%s)\n')
                                % (ids[n], repo[ids[n]], rev, ctx, r, n[:12]))
                    revs.remove(ids[n])
            elif ctx.hex() in ids:
                r = ids[ctx.hex()]
                ui.warn(_('skipping already grafted revision %d:%s '
                          '(was grafted from %d:%s)\n') %
                        (r, repo[r], rev, ctx))
                revs.remove(r)
        if not revs:
            return -1

    for pos, ctx in enumerate(repo.set("%ld", revs)):
        desc = '%d:%s "%s"' % (ctx.rev(), ctx,
                               ctx.description().split('\n', 1)[0])
        names = repo.nodetags(ctx.node()) + repo.nodebookmarks(ctx.node())
        if names:
            desc += ' (%s)' % ' '.join(names)
        ui.status(_('grafting %s\n') % desc)
        if opts.get('dry_run'):
            continue

        source = ctx.extra().get('source')
        extra = {}
        if source:
            extra['source'] = source
            extra['intermediate-source'] = ctx.hex()
        else:
            extra['source'] = ctx.hex()
        user = ctx.user()
        if opts.get('user'):
            user = opts['user']
        date = ctx.date()
        if opts.get('date'):
            date = opts['date']
        message = ctx.description()
        if opts.get('log'):
            message += '\n(grafted from %s)' % ctx.hex()

        # we don't merge the first commit when continuing
        if not cont:
            # perform the graft merge with p1(rev) as 'ancestor'
            try:
                # ui.forcemerge is an internal variable, do not document
                repo.ui.setconfig('ui', 'forcemerge', opts.get('tool', ''),
                                  'graft')
                stats = mergemod.graft(repo, ctx, ctx.p1(),
                                       ['local', 'graft'])
            finally:
                repo.ui.setconfig('ui', 'forcemerge', '', 'graft')
            # report any conflicts
            if stats and stats[3] > 0:
                # write out state for --continue
                nodelines = [repo[rev].hex() + "\n" for rev in revs[pos:]]
                repo.vfs.write('graftstate', ''.join(nodelines))
                extra = ''
                if opts.get('user'):
                    extra += ' --user %s' % util.shellquote(opts['user'])
                if opts.get('date'):
                    extra += ' --date %s' % util.shellquote(opts['date'])
                if opts.get('log'):
                    extra += ' --log'
                hint=_("use 'hg resolve' and 'hg graft --continue%s'") % extra
                raise error.Abort(
                    _("unresolved conflicts, can't continue"),
                    hint=hint)
        else:
            cont = False

        # commit
        node = repo.commit(text=message, user=user,
                    date=date, extra=extra, editor=editor)
        if node is None:
            ui.warn(
                _('note: graft of %d:%s created no changes to commit\n') %
                (ctx.rev(), ctx))

    # remove state when we complete successfully
    if not opts.get('dry_run'):
        util.unlinkpath(repo.join('graftstate'), ignoremissing=True)

    return 0

@command('grep',
    [('0', 'print0', None, _('end fields with NUL')),
    ('', 'all', None, _('print all revisions that match')),
    ('a', 'text', None, _('treat all files as text')),
    ('f', 'follow', None,
     _('follow changeset history,'
       ' or file history across copies and renames')),
    ('i', 'ignore-case', None, _('ignore case when matching')),
    ('l', 'files-with-matches', None,
     _('print only filenames and revisions that match')),
    ('n', 'line-number', None, _('print matching line numbers')),
    ('r', 'rev', [],
     _('only search files changed within revision range'), _('REV')),
    ('u', 'user', None, _('list the author (long with -v)')),
    ('d', 'date', None, _('list the date (short with -q)')),
    ] + formatteropts + walkopts,
    _('[OPTION]... PATTERN [FILE]...'),
    inferrepo=True)
def grep(ui, repo, pattern, *pats, **opts):
    """search revision history for a pattern in specified files

    Search revision history for a regular expression in the specified
    files or the entire project.

    By default, grep prints the most recent revision number for each
    file in which it finds a match. To get it to print every revision
    that contains a change in match status ("-" for a match that becomes
    a non-match, or "+" for a non-match that becomes a match), use the
    --all flag.

    PATTERN can be any Python (roughly Perl-compatible) regular
    expression.

    If no FILEs are specified (and -f/--follow isn't set), all files in
    the repository are searched, including those that don't exist in the
    current branch or have been deleted in a prior changeset.

    Returns 0 if a match is found, 1 otherwise.
    """
    reflags = re.M
    if opts.get('ignore_case'):
        reflags |= re.I
    try:
        regexp = util.re.compile(pattern, reflags)
    except re.error as inst:
        ui.warn(_("grep: invalid match pattern: %s\n") % inst)
        return 1
    sep, eol = ':', '\n'
    if opts.get('print0'):
        sep = eol = '\0'

    getfile = util.lrucachefunc(repo.file)

    def matchlines(body):
        begin = 0
        linenum = 0
        while begin < len(body):
            match = regexp.search(body, begin)
            if not match:
                break
            mstart, mend = match.span()
            linenum += body.count('\n', begin, mstart) + 1
            lstart = body.rfind('\n', begin, mstart) + 1 or begin
            begin = body.find('\n', mend) + 1 or len(body) + 1
            lend = begin - 1
            yield linenum, mstart - lstart, mend - lstart, body[lstart:lend]

    class linestate(object):
        def __init__(self, line, linenum, colstart, colend):
            self.line = line
            self.linenum = linenum
            self.colstart = colstart
            self.colend = colend

        def __hash__(self):
            return hash((self.linenum, self.line))

        def __eq__(self, other):
            return self.line == other.line

        def findpos(self):
            """Iterate all (start, end) indices of matches"""
            yield self.colstart, self.colend
            p = self.colend
            while p < len(self.line):
                m = regexp.search(self.line, p)
                if not m:
                    break
                yield m.span()
                p = m.end()

    matches = {}
    copies = {}
    def grepbody(fn, rev, body):
        matches[rev].setdefault(fn, [])
        m = matches[rev][fn]
        for lnum, cstart, cend, line in matchlines(body):
            s = linestate(line, lnum, cstart, cend)
            m.append(s)

    def difflinestates(a, b):
        sm = difflib.SequenceMatcher(None, a, b)
        for tag, alo, ahi, blo, bhi in sm.get_opcodes():
            if tag == 'insert':
                for i in xrange(blo, bhi):
                    yield ('+', b[i])
            elif tag == 'delete':
                for i in xrange(alo, ahi):
                    yield ('-', a[i])
            elif tag == 'replace':
                for i in xrange(alo, ahi):
                    yield ('-', a[i])
                for i in xrange(blo, bhi):
                    yield ('+', b[i])

    def display(fm, fn, ctx, pstates, states):
        rev = ctx.rev()
        if fm.isplain():
            formatuser = ui.shortuser
        else:
            formatuser = str
        if ui.quiet:
            datefmt = '%Y-%m-%d'
        else:
            datefmt = '%a %b %d %H:%M:%S %Y %1%2'
        found = False
        @util.cachefunc
        def binary():
            flog = getfile(fn)
            return util.binary(flog.read(ctx.filenode(fn)))

        fieldnamemap = {'filename': 'file', 'linenumber': 'line_number'}
        if opts.get('all'):
            iter = difflinestates(pstates, states)
        else:
            iter = [('', l) for l in states]
        for change, l in iter:
            fm.startitem()
            fm.data(node=fm.hexfunc(ctx.node()))
            cols = [
                ('filename', fn, True),
                ('rev', rev, True),
                ('linenumber', l.linenum, opts.get('line_number')),
            ]
            if opts.get('all'):
                cols.append(('change', change, True))
            cols.extend([
                ('user', formatuser(ctx.user()), opts.get('user')),
                ('date', fm.formatdate(ctx.date(), datefmt), opts.get('date')),
            ])
            lastcol = next(name for name, data, cond in reversed(cols) if cond)
            for name, data, cond in cols:
                field = fieldnamemap.get(name, name)
                fm.condwrite(cond, field, '%s', data, label='grep.%s' % name)
                if cond and name != lastcol:
                    fm.plain(sep, label='grep.sep')
            if not opts.get('files_with_matches'):
                fm.plain(sep, label='grep.sep')
                if not opts.get('text') and binary():
                    fm.plain(_(" Binary file matches"))
                else:
                    displaymatches(fm.nested('texts'), l)
            fm.plain(eol)
            found = True
            if opts.get('files_with_matches'):
                break
        return found

    def displaymatches(fm, l):
        p = 0
        for s, e in l.findpos():
            if p < s:
                fm.startitem()
                fm.write('text', '%s', l.line[p:s])
                fm.data(matched=False)
            fm.startitem()
            fm.write('text', '%s', l.line[s:e], label='grep.match')
            fm.data(matched=True)
            p = e
        if p < len(l.line):
            fm.startitem()
            fm.write('text', '%s', l.line[p:])
            fm.data(matched=False)
        fm.end()

    skip = {}
    revfiles = {}
    matchfn = scmutil.match(repo[None], pats, opts)
    found = False
    follow = opts.get('follow')

    def prep(ctx, fns):
        rev = ctx.rev()
        pctx = ctx.p1()
        parent = pctx.rev()
        matches.setdefault(rev, {})
        matches.setdefault(parent, {})
        files = revfiles.setdefault(rev, [])
        for fn in fns:
            flog = getfile(fn)
            try:
                fnode = ctx.filenode(fn)
            except error.LookupError:
                continue

            copied = flog.renamed(fnode)
            copy = follow and copied and copied[0]
            if copy:
                copies.setdefault(rev, {})[fn] = copy
            if fn in skip:
                if copy:
                    skip[copy] = True
                continue
            files.append(fn)

            if fn not in matches[rev]:
                grepbody(fn, rev, flog.read(fnode))

            pfn = copy or fn
            if pfn not in matches[parent]:
                try:
                    fnode = pctx.filenode(pfn)
                    grepbody(pfn, parent, flog.read(fnode))
                except error.LookupError:
                    pass

    fm = ui.formatter('grep', opts)
    for ctx in cmdutil.walkchangerevs(repo, matchfn, opts, prep):
        rev = ctx.rev()
        parent = ctx.p1().rev()
        for fn in sorted(revfiles.get(rev, [])):
            states = matches[rev][fn]
            copy = copies.get(rev, {}).get(fn)
            if fn in skip:
                if copy:
                    skip[copy] = True
                continue
            pstates = matches.get(parent, {}).get(copy or fn, [])
            if pstates or states:
                r = display(fm, fn, ctx, pstates, states)
                found = found or r
                if r and not opts.get('all'):
                    skip[fn] = True
                    if copy:
                        skip[copy] = True
        del matches[rev]
        del revfiles[rev]
    fm.end()

    return not found

@command('heads',
    [('r', 'rev', '',
     _('show only heads which are descendants of STARTREV'), _('STARTREV')),
    ('t', 'topo', False, _('show topological heads only')),
    ('a', 'active', False, _('show active branchheads only (DEPRECATED)')),
    ('c', 'closed', False, _('show normal and closed branch heads')),
    ] + templateopts,
    _('[-ct] [-r STARTREV] [REV]...'))
def heads(ui, repo, *branchrevs, **opts):
    """show branch heads

    With no arguments, show all open branch heads in the repository.
    Branch heads are changesets that have no descendants on the
    same branch. They are where development generally takes place and
    are the usual targets for update and merge operations.

    If one or more REVs are given, only open branch heads on the
    branches associated with the specified changesets are shown. This
    means that you can use :hg:`heads .` to see the heads on the
    currently checked-out branch.

    If -c/--closed is specified, also show branch heads marked closed
    (see :hg:`commit --close-branch`).

    If STARTREV is specified, only those heads that are descendants of
    STARTREV will be displayed.

    If -t/--topo is specified, named branch mechanics will be ignored and only
    topological heads (changesets with no children) will be shown.

    Returns 0 if matching heads are found, 1 if not.
    """

    start = None
    if 'rev' in opts:
        start = scmutil.revsingle(repo, opts['rev'], None).node()

    if opts.get('topo'):
        heads = [repo[h] for h in repo.heads(start)]
    else:
        heads = []
        for branch in repo.branchmap():
            heads += repo.branchheads(branch, start, opts.get('closed'))
        heads = [repo[h] for h in heads]

    if branchrevs:
        branches = set(repo[br].branch() for br in branchrevs)
        heads = [h for h in heads if h.branch() in branches]

    if opts.get('active') and branchrevs:
        dagheads = repo.heads(start)
        heads = [h for h in heads if h.node() in dagheads]

    if branchrevs:
        haveheads = set(h.branch() for h in heads)
        if branches - haveheads:
            headless = ', '.join(b for b in branches - haveheads)
            msg = _('no open branch heads found on branches %s')
            if opts.get('rev'):
                msg += _(' (started at %s)') % opts['rev']
            ui.warn((msg + '\n') % headless)

    if not heads:
        return 1

    heads = sorted(heads, key=lambda x: -x.rev())
    displayer = cmdutil.show_changeset(ui, repo, opts)
    for ctx in heads:
        displayer.show(ctx)
    displayer.close()

@command('help',
    [('e', 'extension', None, _('show only help for extensions')),
     ('c', 'command', None, _('show only help for commands')),
     ('k', 'keyword', None, _('show topics matching keyword')),
     ('s', 'system', [], _('show help for specific platform(s)')),
     ],
    _('[-ecks] [TOPIC]'),
    norepo=True)
def help_(ui, name=None, **opts):
    """show help for a given topic or a help overview

    With no arguments, print a list of commands with short help messages.

    Given a topic, extension, or command name, print help for that
    topic.

    Returns 0 if successful.
    """

    textwidth = ui.configint('ui', 'textwidth', 78)
    termwidth = ui.termwidth() - 2
    if textwidth <= 0 or termwidth < textwidth:
        textwidth = termwidth

    keep = opts.get('system') or []
    if len(keep) == 0:
        if sys.platform.startswith('win'):
            keep.append('windows')
        elif sys.platform == 'OpenVMS':
            keep.append('vms')
        elif sys.platform == 'plan9':
            keep.append('plan9')
        else:
            keep.append('unix')
            keep.append(sys.platform.lower())
    if ui.verbose:
        keep.append('verbose')

    section = None
    subtopic = None
    if name and '.' in name:
        name, remaining = name.split('.', 1)
        remaining = encoding.lower(remaining)
        if '.' in remaining:
            subtopic, section = remaining.split('.', 1)
        else:
            if name in help.subtopics:
                subtopic = remaining
            else:
                section = remaining

    text = help.help_(ui, name, subtopic=subtopic, **opts)

    formatted, pruned = minirst.format(text, textwidth, keep=keep,
                                       section=section)

    # We could have been given a weird ".foo" section without a name
    # to look for, or we could have simply failed to found "foo.bar"
    # because bar isn't a section of foo
    if section and not (formatted and name):
        raise error.Abort(_("help section not found"))

    if 'verbose' in pruned:
        keep.append('omitted')
    else:
        keep.append('notomitted')
    formatted, pruned = minirst.format(text, textwidth, keep=keep,
                                       section=section)
    ui.write(formatted)


@command('identify|id',
    [('r', 'rev', '',
     _('identify the specified revision'), _('REV')),
    ('n', 'num', None, _('show local revision number')),
    ('i', 'id', None, _('show global revision id')),
    ('b', 'branch', None, _('show branch')),
    ('t', 'tags', None, _('show tags')),
    ('B', 'bookmarks', None, _('show bookmarks')),
    ] + remoteopts,
    _('[-nibtB] [-r REV] [SOURCE]'),
    optionalrepo=True)
def identify(ui, repo, source=None, rev=None,
             num=None, id=None, branch=None, tags=None, bookmarks=None, **opts):
    """identify the working directory or specified revision

    Print a summary identifying the repository state at REV using one or
    two parent hash identifiers, followed by a "+" if the working
    directory has uncommitted changes, the branch name (if not default),
    a list of tags, and a list of bookmarks.

    When REV is not given, print a summary of the current state of the
    repository.

    Specifying a path to a repository root or Mercurial bundle will
    cause lookup to operate on that repository/bundle.

    .. container:: verbose

      Examples:

      - generate a build identifier for the working directory::

          hg id --id > build-id.dat

      - find the revision corresponding to a tag::

          hg id -n -r 1.3

      - check the most recent revision of a remote repository::

          hg id -r tip https://www.mercurial-scm.org/repo/hg/

    See :hg:`log` for generating more information about specific revisions,
    including full hash identifiers.

    Returns 0 if successful.
    """

    if not repo and not source:
        raise error.Abort(_("there is no Mercurial repository here "
                           "(.hg not found)"))

    if ui.debugflag:
        hexfunc = hex
    else:
        hexfunc = short
    default = not (num or id or branch or tags or bookmarks)
    output = []
    revs = []

    if source:
        source, branches = hg.parseurl(ui.expandpath(source))
        peer = hg.peer(repo or ui, opts, source) # only pass ui when no repo
        repo = peer.local()
        revs, checkout = hg.addbranchrevs(repo, peer, branches, None)

    if not repo:
        if num or branch or tags:
            raise error.Abort(
                _("can't query remote revision number, branch, or tags"))
        if not rev and revs:
            rev = revs[0]
        if not rev:
            rev = "tip"

        remoterev = peer.lookup(rev)
        if default or id:
            output = [hexfunc(remoterev)]

        def getbms():
            bms = []

            if 'bookmarks' in peer.listkeys('namespaces'):
                hexremoterev = hex(remoterev)
                bms = [bm for bm, bmr in peer.listkeys('bookmarks').iteritems()
                       if bmr == hexremoterev]

            return sorted(bms)

        if bookmarks:
            output.extend(getbms())
        elif default and not ui.quiet:
            # multiple bookmarks for a single parent separated by '/'
            bm = '/'.join(getbms())
            if bm:
                output.append(bm)
    else:
        ctx = scmutil.revsingle(repo, rev, None)

        if ctx.rev() is None:
            ctx = repo[None]
            parents = ctx.parents()
            taglist = []
            for p in parents:
                taglist.extend(p.tags())

            changed = ""
            if default or id or num:
                if (any(repo.status())
                    or any(ctx.sub(s).dirty() for s in ctx.substate)):
                    changed = '+'
            if default or id:
                output = ["%s%s" %
                  ('+'.join([hexfunc(p.node()) for p in parents]), changed)]
            if num:
                output.append("%s%s" %
                  ('+'.join([str(p.rev()) for p in parents]), changed))
        else:
            if default or id:
                output = [hexfunc(ctx.node())]
            if num:
                output.append(str(ctx.rev()))
            taglist = ctx.tags()

        if default and not ui.quiet:
            b = ctx.branch()
            if b != 'default':
                output.append("(%s)" % b)

            # multiple tags for a single parent separated by '/'
            t = '/'.join(taglist)
            if t:
                output.append(t)

            # multiple bookmarks for a single parent separated by '/'
            bm = '/'.join(ctx.bookmarks())
            if bm:
                output.append(bm)
        else:
            if branch:
                output.append(ctx.branch())

            if tags:
                output.extend(taglist)

            if bookmarks:
                output.extend(ctx.bookmarks())

    ui.write("%s\n" % ' '.join(output))

@command('import|patch',
    [('p', 'strip', 1,
     _('directory strip option for patch. This has the same '
       'meaning as the corresponding patch option'), _('NUM')),
    ('b', 'base', '', _('base path (DEPRECATED)'), _('PATH')),
    ('e', 'edit', False, _('invoke editor on commit messages')),
    ('f', 'force', None,
     _('skip check for outstanding uncommitted changes (DEPRECATED)')),
    ('', 'no-commit', None,
     _("don't commit, just update the working directory")),
    ('', 'bypass', None,
     _("apply patch without touching the working directory")),
    ('', 'partial', None,
     _('commit even if some hunks fail')),
    ('', 'exact', None,
     _('abort if patch would apply lossily')),
    ('', 'prefix', '',
     _('apply patch to subdirectory'), _('DIR')),
    ('', 'import-branch', None,
     _('use any branch information in patch (implied by --exact)'))] +
    commitopts + commitopts2 + similarityopts,
    _('[OPTION]... PATCH...'))
def import_(ui, repo, patch1=None, *patches, **opts):
    """import an ordered set of patches

    Import a list of patches and commit them individually (unless
    --no-commit is specified).

    To read a patch from standard input, use "-" as the patch name. If
    a URL is specified, the patch will be downloaded from there.

    Import first applies changes to the working directory (unless
    --bypass is specified), import will abort if there are outstanding
    changes.

    Use --bypass to apply and commit patches directly to the
    repository, without affecting the working directory. Without
    --exact, patches will be applied on top of the working directory
    parent revision.

    You can import a patch straight from a mail message. Even patches
    as attachments work (to use the body part, it must have type
    text/plain or text/x-patch). From and Subject headers of email
    message are used as default committer and commit message. All
    text/plain body parts before first diff are added to the commit
    message.

    If the imported patch was generated by :hg:`export`, user and
    description from patch override values from message headers and
    body. Values given on command line with -m/--message and -u/--user
    override these.

    If --exact is specified, import will set the working directory to
    the parent of each patch before applying it, and will abort if the
    resulting changeset has a different ID than the one recorded in
    the patch. This will guard against various ways that portable
    patch formats and mail systems might fail to transfer Mercurial
    data or metadata. See :hg:`bundle` for lossless transmission.

    Use --partial to ensure a changeset will be created from the patch
    even if some hunks fail to apply. Hunks that fail to apply will be
    written to a <target-file>.rej file. Conflicts can then be resolved
    by hand before :hg:`commit --amend` is run to update the created
    changeset. This flag exists to let people import patches that
    partially apply without losing the associated metadata (author,
    date, description, ...).

    .. note::

       When no hunks apply cleanly, :hg:`import --partial` will create
       an empty changeset, importing only the patch metadata.

    With -s/--similarity, hg will attempt to discover renames and
    copies in the patch in the same way as :hg:`addremove`.

    It is possible to use external patch programs to perform the patch
    by setting the ``ui.patch`` configuration option. For the default
    internal tool, the fuzz can also be configured via ``patch.fuzz``.
    See :hg:`help config` for more information about configuration
    files and how to use these options.

    See :hg:`help dates` for a list of formats valid for -d/--date.

    .. container:: verbose

      Examples:

      - import a traditional patch from a website and detect renames::

          hg import -s 80 http://example.com/bugfix.patch

      - import a changeset from an hgweb server::

          hg import https://www.mercurial-scm.org/repo/hg/rev/5ca8c111e9aa

      - import all the patches in an Unix-style mbox::

          hg import incoming-patches.mbox

      - attempt to exactly restore an exported changeset (not always
        possible)::

          hg import --exact proposed-fix.patch

      - use an external tool to apply a patch which is too fuzzy for
        the default internal tool.

          hg import --config ui.patch="patch --merge" fuzzy.patch

      - change the default fuzzing from 2 to a less strict 7

          hg import --config ui.fuzz=7 fuzz.patch

    Returns 0 on success, 1 on partial success (see --partial).
    """

    if not patch1:
        raise error.Abort(_('need at least one patch to import'))

    patches = (patch1,) + patches

    date = opts.get('date')
    if date:
        opts['date'] = util.parsedate(date)

    exact = opts.get('exact')
    update = not opts.get('bypass')
    if not update and opts.get('no_commit'):
        raise error.Abort(_('cannot use --no-commit with --bypass'))
    try:
        sim = float(opts.get('similarity') or 0)
    except ValueError:
        raise error.Abort(_('similarity must be a number'))
    if sim < 0 or sim > 100:
        raise error.Abort(_('similarity must be between 0 and 100'))
    if sim and not update:
        raise error.Abort(_('cannot use --similarity with --bypass'))
    if exact:
        if opts.get('edit'):
            raise error.Abort(_('cannot use --exact with --edit'))
        if opts.get('prefix'):
            raise error.Abort(_('cannot use --exact with --prefix'))

    base = opts["base"]
    wlock = dsguard = lock = tr = None
    msgs = []
    ret = 0


    try:
        wlock = repo.wlock()

        if update:
            cmdutil.checkunfinished(repo)
            if (exact or not opts.get('force')):
                cmdutil.bailifchanged(repo)

        if not opts.get('no_commit'):
            lock = repo.lock()
            tr = repo.transaction('import')
        else:
            dsguard = cmdutil.dirstateguard(repo, 'import')
        parents = repo[None].parents()
        for patchurl in patches:
            if patchurl == '-':
                ui.status(_('applying patch from stdin\n'))
                patchfile = ui.fin
                patchurl = 'stdin'      # for error message
            else:
                patchurl = os.path.join(base, patchurl)
                ui.status(_('applying %s\n') % patchurl)
                patchfile = hg.openpath(ui, patchurl)

            haspatch = False
            for hunk in patch.split(patchfile):
                (msg, node, rej) = cmdutil.tryimportone(ui, repo, hunk,
                                                        parents, opts,
                                                        msgs, hg.clean)
                if msg:
                    haspatch = True
                    ui.note(msg + '\n')
                if update or exact:
                    parents = repo[None].parents()
                else:
                    parents = [repo[node]]
                if rej:
                    ui.write_err(_("patch applied partially\n"))
                    ui.write_err(_("(fix the .rej files and run "
                                   "`hg commit --amend`)\n"))
                    ret = 1
                    break

            if not haspatch:
                raise error.Abort(_('%s: no diffs found') % patchurl)

        if tr:
            tr.close()
        if msgs:
            repo.savecommitmessage('\n* * *\n'.join(msgs))
        if dsguard:
            dsguard.close()
        return ret
    finally:
        if tr:
            tr.release()
        release(lock, dsguard, wlock)

@command('incoming|in',
    [('f', 'force', None,
     _('run even if remote repository is unrelated')),
    ('n', 'newest-first', None, _('show newest record first')),
    ('', 'bundle', '',
     _('file to store the bundles into'), _('FILE')),
    ('r', 'rev', [], _('a remote changeset intended to be added'), _('REV')),
    ('B', 'bookmarks', False, _("compare bookmarks")),
    ('b', 'branch', [],
     _('a specific branch you would like to pull'), _('BRANCH')),
    ] + logopts + remoteopts + subrepoopts,
    _('[-p] [-n] [-M] [-f] [-r REV]... [--bundle FILENAME] [SOURCE]'))
def incoming(ui, repo, source="default", **opts):
    """show new changesets found in source

    Show new changesets found in the specified path/URL or the default
    pull location. These are the changesets that would have been pulled
    if a pull at the time you issued this command.

    See pull for valid source format details.

    .. container:: verbose

      With -B/--bookmarks, the result of bookmark comparison between
      local and remote repositories is displayed. With -v/--verbose,
      status is also displayed for each bookmark like below::

        BM1               01234567890a added
        BM2               1234567890ab advanced
        BM3               234567890abc diverged
        BM4               34567890abcd changed

      The action taken locally when pulling depends on the
      status of each bookmark:

      :``added``: pull will create it
      :``advanced``: pull will update it
      :``diverged``: pull will create a divergent bookmark
      :``changed``: result depends on remote changesets

      From the point of view of pulling behavior, bookmark
      existing only in the remote repository are treated as ``added``,
      even if it is in fact locally deleted.

    .. container:: verbose

      For remote repository, using --bundle avoids downloading the
      changesets twice if the incoming is followed by a pull.

      Examples:

      - show incoming changes with patches and full description::

          hg incoming -vp

      - show incoming changes excluding merges, store a bundle::

          hg in -vpM --bundle incoming.hg
          hg pull incoming.hg

      - briefly list changes inside a bundle::

          hg in changes.hg -T "{desc|firstline}\\n"

    Returns 0 if there are incoming changes, 1 otherwise.
    """
    if opts.get('graph'):
        cmdutil.checkunsupportedgraphflags([], opts)
        def display(other, chlist, displayer):
            revdag = cmdutil.graphrevs(other, chlist, opts)
            cmdutil.displaygraph(ui, repo, revdag, displayer,
                                 graphmod.asciiedges)

        hg._incoming(display, lambda: 1, ui, repo, source, opts, buffered=True)
        return 0

    if opts.get('bundle') and opts.get('subrepos'):
        raise error.Abort(_('cannot combine --bundle and --subrepos'))

    if opts.get('bookmarks'):
        source, branches = hg.parseurl(ui.expandpath(source),
                                       opts.get('branch'))
        other = hg.peer(repo, opts, source)
        if 'bookmarks' not in other.listkeys('namespaces'):
            ui.warn(_("remote doesn't support bookmarks\n"))
            return 0
        ui.status(_('comparing with %s\n') % util.hidepassword(source))
        return bookmarks.incoming(ui, repo, other)

    repo._subtoppath = ui.expandpath(source)
    try:
        return hg.incoming(ui, repo, source, opts)
    finally:
        del repo._subtoppath


@command('^init', remoteopts, _('[-e CMD] [--remotecmd CMD] [DEST]'),
         norepo=True)
def init(ui, dest=".", **opts):
    """create a new repository in the given directory

    Initialize a new repository in the given directory. If the given
    directory does not exist, it will be created.

    If no directory is given, the current directory is used.

    It is possible to specify an ``ssh://`` URL as the destination.
    See :hg:`help urls` for more information.

    Returns 0 on success.
    """
    hg.peer(ui, opts, ui.expandpath(dest), create=True)

@command('locate',
    [('r', 'rev', '', _('search the repository as it is in REV'), _('REV')),
    ('0', 'print0', None, _('end filenames with NUL, for use with xargs')),
    ('f', 'fullpath', None, _('print complete paths from the filesystem root')),
    ] + walkopts,
    _('[OPTION]... [PATTERN]...'))
def locate(ui, repo, *pats, **opts):
    """locate files matching specific patterns (DEPRECATED)

    Print files under Mercurial control in the working directory whose
    names match the given patterns.

    By default, this command searches all directories in the working
    directory. To search just the current directory and its
    subdirectories, use "--include .".

    If no patterns are given to match, this command prints the names
    of all files under Mercurial control in the working directory.

    If you want to feed the output of this command into the "xargs"
    command, use the -0 option to both this command and "xargs". This
    will avoid the problem of "xargs" treating single filenames that
    contain whitespace as multiple filenames.

    See :hg:`help files` for a more versatile command.

    Returns 0 if a match is found, 1 otherwise.
    """
    if opts.get('print0'):
        end = '\0'
    else:
        end = '\n'
    rev = scmutil.revsingle(repo, opts.get('rev'), None).node()

    ret = 1
    ctx = repo[rev]
    m = scmutil.match(ctx, pats, opts, default='relglob',
                      badfn=lambda x, y: False)

    for abs in ctx.matches(m):
        if opts.get('fullpath'):
            ui.write(repo.wjoin(abs), end)
        else:
            ui.write(((pats and m.rel(abs)) or abs), end)
        ret = 0

    return ret

@command('^log|history',
    [('f', 'follow', None,
     _('follow changeset history, or file history across copies and renames')),
    ('', 'follow-first', None,
     _('only follow the first parent of merge changesets (DEPRECATED)')),
    ('d', 'date', '', _('show revisions matching date spec'), _('DATE')),
    ('C', 'copies', None, _('show copied files')),
    ('k', 'keyword', [],
     _('do case-insensitive search for a given text'), _('TEXT')),
    ('r', 'rev', [], _('show the specified revision or revset'), _('REV')),
    ('', 'removed', None, _('include revisions where files were removed')),
    ('m', 'only-merges', None, _('show only merges (DEPRECATED)')),
    ('u', 'user', [], _('revisions committed by user'), _('USER')),
    ('', 'only-branch', [],
     _('show only changesets within the given named branch (DEPRECATED)'),
     _('BRANCH')),
    ('b', 'branch', [],
     _('show changesets within the given named branch'), _('BRANCH')),
    ('P', 'prune', [],
     _('do not display revision or any of its ancestors'), _('REV')),
    ] + logopts + walkopts,
    _('[OPTION]... [FILE]'),
    inferrepo=True)
def log(ui, repo, *pats, **opts):
    """show revision history of entire repository or files

    Print the revision history of the specified files or the entire
    project.

    If no revision range is specified, the default is ``tip:0`` unless
    --follow is set, in which case the working directory parent is
    used as the starting revision.

    File history is shown without following rename or copy history of
    files. Use -f/--follow with a filename to follow history across
    renames and copies. --follow without a filename will only show
    ancestors or descendants of the starting revision.

    By default this command prints revision number and changeset id,
    tags, non-trivial parents, user, date and time, and a summary for
    each commit. When the -v/--verbose switch is used, the list of
    changed files and full commit message are shown.

    With --graph the revisions are shown as an ASCII art DAG with the most
    recent changeset at the top.
    'o' is a changeset, '@' is a working directory parent, 'x' is obsolete,
    and '+' represents a fork where the changeset from the lines below is a
    parent of the 'o' merge on the same line.

    .. note::

       :hg:`log --patch` may generate unexpected diff output for merge
       changesets, as it will only compare the merge changeset against
       its first parent. Also, only files different from BOTH parents
       will appear in files:.

    .. note::

       For performance reasons, :hg:`log FILE` may omit duplicate changes
       made on branches and will not show removals or mode changes. To
       see all such changes, use the --removed switch.

    .. container:: verbose

      Some examples:

      - changesets with full descriptions and file lists::

          hg log -v

      - changesets ancestral to the working directory::

          hg log -f

      - last 10 commits on the current branch::

          hg log -l 10 -b .

      - changesets showing all modifications of a file, including removals::

          hg log --removed file.c

      - all changesets that touch a directory, with diffs, excluding merges::

          hg log -Mp lib/

      - all revision numbers that match a keyword::

          hg log -k bug --template "{rev}\\n"

      - the full hash identifier of the working directory parent::

          hg log -r . --template "{node}\\n"

      - list available log templates::

          hg log -T list

      - check if a given changeset is included in a tagged release::

          hg log -r "a21ccf and ancestor(1.9)"

      - find all changesets by some user in a date range::

          hg log -k alice -d "may 2008 to jul 2008"

      - summary of all changesets after the last tag::

          hg log -r "last(tagged())::" --template "{desc|firstline}\\n"

    See :hg:`help dates` for a list of formats valid for -d/--date.

    See :hg:`help revisions` and :hg:`help revsets` for more about
    specifying and ordering revisions.

    See :hg:`help templates` for more about pre-packaged styles and
    specifying custom templates.

    Returns 0 on success.

    """
    if opts.get('follow') and opts.get('rev'):
        opts['rev'] = [revset.formatspec('reverse(::%lr)', opts.get('rev'))]
        del opts['follow']

    if opts.get('graph'):
        return cmdutil.graphlog(ui, repo, *pats, **opts)

    revs, expr, filematcher = cmdutil.getlogrevs(repo, pats, opts)
    limit = cmdutil.loglimit(opts)
    count = 0

    getrenamed = None
    if opts.get('copies'):
        endrev = None
        if opts.get('rev'):
            endrev = scmutil.revrange(repo, opts.get('rev')).max() + 1
        getrenamed = templatekw.getrenamedfn(repo, endrev=endrev)

    displayer = cmdutil.show_changeset(ui, repo, opts, buffered=True)
    for rev in revs:
        if count == limit:
            break
        ctx = repo[rev]
        copies = None
        if getrenamed is not None and rev:
            copies = []
            for fn in ctx.files():
                rename = getrenamed(fn, rev)
                if rename:
                    copies.append((fn, rename[0]))
        if filematcher:
            revmatchfn = filematcher(ctx.rev())
        else:
            revmatchfn = None
        displayer.show(ctx, copies=copies, matchfn=revmatchfn)
        if displayer.flush(ctx):
            count += 1

    displayer.close()

@command('manifest',
    [('r', 'rev', '', _('revision to display'), _('REV')),
     ('', 'all', False, _("list files from all revisions"))]
         + formatteropts,
    _('[-r REV]'))
def manifest(ui, repo, node=None, rev=None, **opts):
    """output the current or given revision of the project manifest

    Print a list of version controlled files for the given revision.
    If no revision is given, the first parent of the working directory
    is used, or the null revision if no revision is checked out.

    With -v, print file permissions, symlink and executable bits.
    With --debug, print file revision hashes.

    If option --all is specified, the list of all files from all revisions
    is printed. This includes deleted and renamed files.

    Returns 0 on success.
    """

    fm = ui.formatter('manifest', opts)

    if opts.get('all'):
        if rev or node:
            raise error.Abort(_("can't specify a revision with --all"))

        res = []
        prefix = "data/"
        suffix = ".i"
        plen = len(prefix)
        slen = len(suffix)
        with repo.lock():
            for fn, b, size in repo.store.datafiles():
                if size != 0 and fn[-slen:] == suffix and fn[:plen] == prefix:
                    res.append(fn[plen:-slen])
        for f in res:
            fm.startitem()
            fm.write("path", '%s\n', f)
        fm.end()
        return

    if rev and node:
        raise error.Abort(_("please specify just one revision"))

    if not node:
        node = rev

    char = {'l': '@', 'x': '*', '': ''}
    mode = {'l': '644', 'x': '755', '': '644'}
    ctx = scmutil.revsingle(repo, node)
    mf = ctx.manifest()
    for f in ctx:
        fm.startitem()
        fl = ctx[f].flags()
        fm.condwrite(ui.debugflag, 'hash', '%s ', hex(mf[f]))
        fm.condwrite(ui.verbose, 'mode type', '%s %1s ', mode[fl], char[fl])
        fm.write('path', '%s\n', f)
    fm.end()

@command('^merge',
    [('f', 'force', None,
      _('force a merge including outstanding changes (DEPRECATED)')),
    ('r', 'rev', '', _('revision to merge'), _('REV')),
    ('P', 'preview', None,
     _('review revisions to merge (no merge is performed)'))
     ] + mergetoolopts,
    _('[-P] [[-r] REV]'))
def merge(ui, repo, node=None, **opts):
    """merge another revision into working directory

    The current working directory is updated with all changes made in
    the requested revision since the last common predecessor revision.

    Files that changed between either parent are marked as changed for
    the next commit and a commit must be performed before any further
    updates to the repository are allowed. The next commit will have
    two parents.

    ``--tool`` can be used to specify the merge tool used for file
    merges. It overrides the HGMERGE environment variable and your
    configuration files. See :hg:`help merge-tools` for options.

    If no revision is specified, the working directory's parent is a
    head revision, and the current branch contains exactly one other
    head, the other head is merged with by default. Otherwise, an
    explicit revision with which to merge with must be provided.

    See :hg:`help resolve` for information on handling file conflicts.

    To undo an uncommitted merge, use :hg:`update --clean .` which
    will check out a clean copy of the original merge parent, losing
    all changes.

    Returns 0 on success, 1 if there are unresolved files.
    """

    if opts.get('rev') and node:
        raise error.Abort(_("please specify just one revision"))
    if not node:
        node = opts.get('rev')

    if node:
        node = scmutil.revsingle(repo, node).node()

    if not node:
        node = repo[destutil.destmerge(repo)].node()

    if opts.get('preview'):
        # find nodes that are ancestors of p2 but not of p1
        p1 = repo.lookup('.')
        p2 = repo.lookup(node)
        nodes = repo.changelog.findmissing(common=[p1], heads=[p2])

        displayer = cmdutil.show_changeset(ui, repo, opts)
        for node in nodes:
            displayer.show(repo[node])
        displayer.close()
        return 0

    try:
        # ui.forcemerge is an internal variable, do not document
        repo.ui.setconfig('ui', 'forcemerge', opts.get('tool', ''), 'merge')
        force = opts.get('force')
        labels = ['working copy', 'merge rev']
        return hg.merge(repo, node, force=force, mergeforce=force,
                        labels=labels)
    finally:
        ui.setconfig('ui', 'forcemerge', '', 'merge')

@command('outgoing|out',
    [('f', 'force', None, _('run even when the destination is unrelated')),
    ('r', 'rev', [],
     _('a changeset intended to be included in the destination'), _('REV')),
    ('n', 'newest-first', None, _('show newest record first')),
    ('B', 'bookmarks', False, _('compare bookmarks')),
    ('b', 'branch', [], _('a specific branch you would like to push'),
     _('BRANCH')),
    ] + logopts + remoteopts + subrepoopts,
    _('[-M] [-p] [-n] [-f] [-r REV]... [DEST]'))
def outgoing(ui, repo, dest=None, **opts):
    """show changesets not found in the destination

    Show changesets not found in the specified destination repository
    or the default push location. These are the changesets that would
    be pushed if a push was requested.

    See pull for details of valid destination formats.

    .. container:: verbose

      With -B/--bookmarks, the result of bookmark comparison between
      local and remote repositories is displayed. With -v/--verbose,
      status is also displayed for each bookmark like below::

        BM1               01234567890a added
        BM2                            deleted
        BM3               234567890abc advanced
        BM4               34567890abcd diverged
        BM5               4567890abcde changed

      The action taken when pushing depends on the
      status of each bookmark:

      :``added``: push with ``-B`` will create it
      :``deleted``: push with ``-B`` will delete it
      :``advanced``: push will update it
      :``diverged``: push with ``-B`` will update it
      :``changed``: push with ``-B`` will update it

      From the point of view of pushing behavior, bookmarks
      existing only in the remote repository are treated as
      ``deleted``, even if it is in fact added remotely.

    Returns 0 if there are outgoing changes, 1 otherwise.
    """
    if opts.get('graph'):
        cmdutil.checkunsupportedgraphflags([], opts)
        o, other = hg._outgoing(ui, repo, dest, opts)
        if not o:
            cmdutil.outgoinghooks(ui, repo, other, opts, o)
            return

        revdag = cmdutil.graphrevs(repo, o, opts)
        displayer = cmdutil.show_changeset(ui, repo, opts, buffered=True)
        cmdutil.displaygraph(ui, repo, revdag, displayer, graphmod.asciiedges)
        cmdutil.outgoinghooks(ui, repo, other, opts, o)
        return 0

    if opts.get('bookmarks'):
        dest = ui.expandpath(dest or 'default-push', dest or 'default')
        dest, branches = hg.parseurl(dest, opts.get('branch'))
        other = hg.peer(repo, opts, dest)
        if 'bookmarks' not in other.listkeys('namespaces'):
            ui.warn(_("remote doesn't support bookmarks\n"))
            return 0
        ui.status(_('comparing with %s\n') % util.hidepassword(dest))
        return bookmarks.outgoing(ui, repo, other)

    repo._subtoppath = ui.expandpath(dest or 'default-push', dest or 'default')
    try:
        return hg.outgoing(ui, repo, dest, opts)
    finally:
        del repo._subtoppath

@command('parents',
    [('r', 'rev', '', _('show parents of the specified revision'), _('REV')),
    ] + templateopts,
    _('[-r REV] [FILE]'),
    inferrepo=True)
def parents(ui, repo, file_=None, **opts):
    """show the parents of the working directory or revision (DEPRECATED)

    Print the working directory's parent revisions. If a revision is
    given via -r/--rev, the parent of that revision will be printed.
    If a file argument is given, the revision in which the file was
    last changed (before the working directory revision or the
    argument to --rev if given) is printed.

    This command is equivalent to::

        hg log -r "p1()+p2()" or
        hg log -r "p1(REV)+p2(REV)" or
        hg log -r "max(::p1() and file(FILE))+max(::p2() and file(FILE))" or
        hg log -r "max(::p1(REV) and file(FILE))+max(::p2(REV) and file(FILE))"

    See :hg:`summary` and :hg:`help revsets` for related information.

    Returns 0 on success.
    """

    ctx = scmutil.revsingle(repo, opts.get('rev'), None)

    if file_:
        m = scmutil.match(ctx, (file_,), opts)
        if m.anypats() or len(m.files()) != 1:
            raise error.Abort(_('can only specify an explicit filename'))
        file_ = m.files()[0]
        filenodes = []
        for cp in ctx.parents():
            if not cp:
                continue
            try:
                filenodes.append(cp.filenode(file_))
            except error.LookupError:
                pass
        if not filenodes:
            raise error.Abort(_("'%s' not found in manifest!") % file_)
        p = []
        for fn in filenodes:
            fctx = repo.filectx(file_, fileid=fn)
            p.append(fctx.node())
    else:
        p = [cp.node() for cp in ctx.parents()]

    displayer = cmdutil.show_changeset(ui, repo, opts)
    for n in p:
        if n != nullid:
            displayer.show(repo[n])
    displayer.close()

@command('paths', formatteropts, _('[NAME]'), optionalrepo=True)
def paths(ui, repo, search=None, **opts):
    """show aliases for remote repositories

    Show definition of symbolic path name NAME. If no name is given,
    show definition of all available names.

    Option -q/--quiet suppresses all output when searching for NAME
    and shows only the path names when listing all definitions.

    Path names are defined in the [paths] section of your
    configuration file and in ``/etc/mercurial/hgrc``. If run inside a
    repository, ``.hg/hgrc`` is used, too.

    The path names ``default`` and ``default-push`` have a special
    meaning.  When performing a push or pull operation, they are used
    as fallbacks if no location is specified on the command-line.
    When ``default-push`` is set, it will be used for push and
    ``default`` will be used for pull; otherwise ``default`` is used
    as the fallback for both.  When cloning a repository, the clone
    source is written as ``default`` in ``.hg/hgrc``.

    .. note::

       ``default`` and ``default-push`` apply to all inbound (e.g.
       :hg:`incoming`) and outbound (e.g. :hg:`outgoing`, :hg:`email`
       and :hg:`bundle`) operations.

    See :hg:`help urls` for more information.

    Returns 0 on success.
    """
    if search:
        pathitems = [(name, path) for name, path in ui.paths.iteritems()
                     if name == search]
    else:
        pathitems = sorted(ui.paths.iteritems())

    fm = ui.formatter('paths', opts)
    if fm.isplain():
        hidepassword = util.hidepassword
    else:
        hidepassword = str
    if ui.quiet:
        namefmt = '%s\n'
    else:
        namefmt = '%s = '
    showsubopts = not search and not ui.quiet

    for name, path in pathitems:
        fm.startitem()
        fm.condwrite(not search, 'name', namefmt, name)
        fm.condwrite(not ui.quiet, 'url', '%s\n', hidepassword(path.rawloc))
        for subopt, value in sorted(path.suboptions.items()):
            assert subopt not in ('name', 'url')
            if showsubopts:
                fm.plain('%s:%s = ' % (name, subopt))
            fm.condwrite(showsubopts, subopt, '%s\n', value)

    fm.end()

    if search and not pathitems:
        if not ui.quiet:
            ui.warn(_("not found!\n"))
        return 1
    else:
        return 0

@command('phase',
    [('p', 'public', False, _('set changeset phase to public')),
     ('d', 'draft', False, _('set changeset phase to draft')),
     ('s', 'secret', False, _('set changeset phase to secret')),
     ('f', 'force', False, _('allow to move boundary backward')),
     ('r', 'rev', [], _('target revision'), _('REV')),
    ],
    _('[-p|-d|-s] [-f] [-r] [REV...]'))
def phase(ui, repo, *revs, **opts):
    """set or show the current phase name

    With no argument, show the phase name of the current revision(s).

    With one of -p/--public, -d/--draft or -s/--secret, change the
    phase value of the specified revisions.

    Unless -f/--force is specified, :hg:`phase` won't move changeset from a
    lower phase to an higher phase. Phases are ordered as follows::

        public < draft < secret

    Returns 0 on success, 1 if some phases could not be changed.

    (For more information about the phases concept, see :hg:`help phases`.)
    """
    # search for a unique phase argument
    targetphase = None
    for idx, name in enumerate(phases.phasenames):
        if opts[name]:
            if targetphase is not None:
                raise error.Abort(_('only one phase can be specified'))
            targetphase = idx

    # look for specified revision
    revs = list(revs)
    revs.extend(opts['rev'])
    if not revs:
        # display both parents as the second parent phase can influence
        # the phase of a merge commit
        revs = [c.rev() for c in repo[None].parents()]

    revs = scmutil.revrange(repo, revs)

    lock = None
    ret = 0
    if targetphase is None:
        # display
        for r in revs:
            ctx = repo[r]
            ui.write('%i: %s\n' % (ctx.rev(), ctx.phasestr()))
    else:
        tr = None
        lock = repo.lock()
        try:
            tr = repo.transaction("phase")
            # set phase
            if not revs:
                raise error.Abort(_('empty revision set'))
            nodes = [repo[r].node() for r in revs]
            # moving revision from public to draft may hide them
            # We have to check result on an unfiltered repository
            unfi = repo.unfiltered()
            getphase = unfi._phasecache.phase
            olddata = [getphase(unfi, r) for r in unfi]
            phases.advanceboundary(repo, tr, targetphase, nodes)
            if opts['force']:
                phases.retractboundary(repo, tr, targetphase, nodes)
            tr.close()
        finally:
            if tr is not None:
                tr.release()
            lock.release()
        getphase = unfi._phasecache.phase
        newdata = [getphase(unfi, r) for r in unfi]
        changes = sum(newdata[r] != olddata[r] for r in unfi)
        cl = unfi.changelog
        rejected = [n for n in nodes
                    if newdata[cl.rev(n)] < targetphase]
        if rejected:
            ui.warn(_('cannot move %i changesets to a higher '
                      'phase, use --force\n') % len(rejected))
            ret = 1
        if changes:
            msg = _('phase changed for %i changesets\n') % changes
            if ret:
                ui.status(msg)
            else:
                ui.note(msg)
        else:
            ui.warn(_('no phases changed\n'))
    return ret

def postincoming(ui, repo, modheads, optupdate, checkout, brev):
    """Run after a changegroup has been added via pull/unbundle

    This takes arguments below:

    :modheads: change of heads by pull/unbundle
    :optupdate: updating working directory is needed or not
    :checkout: update destination revision (or None to default destination)
    :brev: a name, which might be a bookmark to be activated after updating
    """
    if modheads == 0:
        return
    if optupdate:
        try:
            return hg.updatetotally(ui, repo, checkout, brev)
        except error.UpdateAbort as inst:
            msg = _("not updating: %s") % str(inst)
            hint = inst.hint
            raise error.UpdateAbort(msg, hint=hint)
    if modheads > 1:
        currentbranchheads = len(repo.branchheads())
        if currentbranchheads == modheads:
            ui.status(_("(run 'hg heads' to see heads, 'hg merge' to merge)\n"))
        elif currentbranchheads > 1:
            ui.status(_("(run 'hg heads .' to see heads, 'hg merge' to "
                        "merge)\n"))
        else:
            ui.status(_("(run 'hg heads' to see heads)\n"))
    else:
        ui.status(_("(run 'hg update' to get a working copy)\n"))

@command('^pull',
    [('u', 'update', None,
     _('update to new branch head if changesets were pulled')),
    ('f', 'force', None, _('run even when remote repository is unrelated')),
    ('r', 'rev', [], _('a remote changeset intended to be added'), _('REV')),
    ('B', 'bookmark', [], _("bookmark to pull"), _('BOOKMARK')),
    ('b', 'branch', [], _('a specific branch you would like to pull'),
     _('BRANCH')),
    ] + remoteopts,
    _('[-u] [-f] [-r REV]... [-e CMD] [--remotecmd CMD] [SOURCE]'))
def pull(ui, repo, source="default", **opts):
    """pull changes from the specified source

    Pull changes from a remote repository to a local one.

    This finds all changes from the repository at the specified path
    or URL and adds them to a local repository (the current one unless
    -R is specified). By default, this does not update the copy of the
    project in the working directory.

    Use :hg:`incoming` if you want to see what would have been added
    by a pull at the time you issued this command. If you then decide
    to add those changes to the repository, you should use :hg:`pull
    -r X` where ``X`` is the last changeset listed by :hg:`incoming`.

    If SOURCE is omitted, the 'default' path will be used.
    See :hg:`help urls` for more information.

    Specifying bookmark as ``.`` is equivalent to specifying the active
    bookmark's name.

    Returns 0 on success, 1 if an update had unresolved files.
    """
    source, branches = hg.parseurl(ui.expandpath(source), opts.get('branch'))
    ui.status(_('pulling from %s\n') % util.hidepassword(source))
    other = hg.peer(repo, opts, source)
    try:
        revs, checkout = hg.addbranchrevs(repo, other, branches,
                                          opts.get('rev'))


        pullopargs = {}
        if opts.get('bookmark'):
            if not revs:
                revs = []
            # The list of bookmark used here is not the one used to actually
            # update the bookmark name. This can result in the revision pulled
            # not ending up with the name of the bookmark because of a race
            # condition on the server. (See issue 4689 for details)
            remotebookmarks = other.listkeys('bookmarks')
            pullopargs['remotebookmarks'] = remotebookmarks
            for b in opts['bookmark']:
                b = repo._bookmarks.expandname(b)
                if b not in remotebookmarks:
                    raise error.Abort(_('remote bookmark %s not found!') % b)
                revs.append(remotebookmarks[b])

        if revs:
            try:
                # When 'rev' is a bookmark name, we cannot guarantee that it
                # will be updated with that name because of a race condition
                # server side. (See issue 4689 for details)
                oldrevs = revs
                revs = [] # actually, nodes
                for r in oldrevs:
                    node = other.lookup(r)
                    revs.append(node)
                    if r == checkout:
                        checkout = node
            except error.CapabilityError:
                err = _("other repository doesn't support revision lookup, "
                        "so a rev cannot be specified.")
                raise error.Abort(err)

        pullopargs.update(opts.get('opargs', {}))
        modheads = exchange.pull(repo, other, heads=revs,
                                 force=opts.get('force'),
                                 bookmarks=opts.get('bookmark', ()),
                                 opargs=pullopargs).cgresult

        # brev is a name, which might be a bookmark to be activated at
        # the end of the update. In other words, it is an explicit
        # destination of the update
        brev = None

        if checkout:
            checkout = str(repo.changelog.rev(checkout))

            # order below depends on implementation of
            # hg.addbranchrevs(). opts['bookmark'] is ignored,
            # because 'checkout' is determined without it.
            if opts.get('rev'):
                brev = opts['rev'][0]
            elif opts.get('branch'):
                brev = opts['branch'][0]
            else:
                brev = branches[0]
        repo._subtoppath = source
        try:
            ret = postincoming(ui, repo, modheads, opts.get('update'),
                               checkout, brev)

        finally:
            del repo._subtoppath

    finally:
        other.close()
    return ret

@command('^push',
    [('f', 'force', None, _('force push')),
    ('r', 'rev', [],
     _('a changeset intended to be included in the destination'),
     _('REV')),
    ('B', 'bookmark', [], _("bookmark to push"), _('BOOKMARK')),
    ('b', 'branch', [],
     _('a specific branch you would like to push'), _('BRANCH')),
    ('', 'new-branch', False, _('allow pushing a new branch')),
    ] + remoteopts,
    _('[-f] [-r REV]... [-e CMD] [--remotecmd CMD] [DEST]'))
def push(ui, repo, dest=None, **opts):
    """push changes to the specified destination

    Push changesets from the local repository to the specified
    destination.

    This operation is symmetrical to pull: it is identical to a pull
    in the destination repository from the current one.

    By default, push will not allow creation of new heads at the
    destination, since multiple heads would make it unclear which head
    to use. In this situation, it is recommended to pull and merge
    before pushing.

    Use --new-branch if you want to allow push to create a new named
    branch that is not present at the destination. This allows you to
    only create a new branch without forcing other changes.

    .. note::

       Extra care should be taken with the -f/--force option,
       which will push all new heads on all branches, an action which will
       almost always cause confusion for collaborators.

    If -r/--rev is used, the specified revision and all its ancestors
    will be pushed to the remote repository.

    If -B/--bookmark is used, the specified bookmarked revision, its
    ancestors, and the bookmark will be pushed to the remote
    repository. Specifying ``.`` is equivalent to specifying the active
    bookmark's name.

    Please see :hg:`help urls` for important details about ``ssh://``
    URLs. If DESTINATION is omitted, a default path will be used.

    Returns 0 if push was successful, 1 if nothing to push.
    """

    if opts.get('bookmark'):
        ui.setconfig('bookmarks', 'pushing', opts['bookmark'], 'push')
        for b in opts['bookmark']:
            # translate -B options to -r so changesets get pushed
            b = repo._bookmarks.expandname(b)
            if b in repo._bookmarks:
                opts.setdefault('rev', []).append(b)
            else:
                # if we try to push a deleted bookmark, translate it to null
                # this lets simultaneous -r, -b options continue working
                opts.setdefault('rev', []).append("null")

    path = ui.paths.getpath(dest, default=('default-push', 'default'))
    if not path:
        raise error.Abort(_('default repository not configured!'),
                         hint=_("see 'hg help config.paths'"))
    dest = path.pushloc or path.loc
    branches = (path.branch, opts.get('branch') or [])
    ui.status(_('pushing to %s\n') % util.hidepassword(dest))
    revs, checkout = hg.addbranchrevs(repo, repo, branches, opts.get('rev'))
    other = hg.peer(repo, opts, dest)

    if revs:
        revs = [repo.lookup(r) for r in scmutil.revrange(repo, revs)]
        if not revs:
            raise error.Abort(_("specified revisions evaluate to an empty set"),
                             hint=_("use different revision arguments"))
    elif path.pushrev:
        # It doesn't make any sense to specify ancestor revisions. So limit
        # to DAG heads to make discovery simpler.
        expr = revset.formatspec('heads(%r)', path.pushrev)
        revs = scmutil.revrange(repo, [expr])
        revs = [repo[rev].node() for rev in revs]
        if not revs:
            raise error.Abort(_('default push revset for path evaluates to an '
                                'empty set'))

    repo._subtoppath = dest
    try:
        # push subrepos depth-first for coherent ordering
        c = repo['']
        subs = c.substate # only repos that are committed
        for s in sorted(subs):
            result = c.sub(s).push(opts)
            if result == 0:
                return not result
    finally:
        del repo._subtoppath
    pushop = exchange.push(repo, other, opts.get('force'), revs=revs,
                           newbranch=opts.get('new_branch'),
                           bookmarks=opts.get('bookmark', ()),
                           opargs=opts.get('opargs'))

    result = not pushop.cgresult

    if pushop.bkresult is not None:
        if pushop.bkresult == 2:
            result = 2
        elif not result and pushop.bkresult:
            result = 2

    return result

@command('recover', [])
def recover(ui, repo):
    """roll back an interrupted transaction

    Recover from an interrupted commit or pull.

    This command tries to fix the repository status after an
    interrupted operation. It should only be necessary when Mercurial
    suggests it.

    Returns 0 if successful, 1 if nothing to recover or verify fails.
    """
    if repo.recover():
        return hg.verify(repo)
    return 1

@command('^remove|rm',
    [('A', 'after', None, _('record delete for missing files')),
    ('f', 'force', None,
     _('forget added files, delete modified files')),
    ] + subrepoopts + walkopts,
    _('[OPTION]... FILE...'),
    inferrepo=True)
def remove(ui, repo, *pats, **opts):
    """remove the specified files on the next commit

    Schedule the indicated files for removal from the current branch.

    This command schedules the files to be removed at the next commit.
    To undo a remove before that, see :hg:`revert`. To undo added
    files, see :hg:`forget`.

    .. container:: verbose

      -A/--after can be used to remove only files that have already
      been deleted, -f/--force can be used to force deletion, and -Af
      can be used to remove files from the next revision without
      deleting them from the working directory.

      The following table details the behavior of remove for different
      file states (columns) and option combinations (rows). The file
      states are Added [A], Clean [C], Modified [M] and Missing [!]
      (as reported by :hg:`status`). The actions are Warn, Remove
      (from branch) and Delete (from disk):

      ========= == == == ==
      opt/state A  C  M  !
      ========= == == == ==
      none      W  RD W  R
      -f        R  RD RD R
      -A        W  W  W  R
      -Af       R  R  R  R
      ========= == == == ==

      .. note::

         :hg:`remove` never deletes files in Added [A] state from the
         working directory, not even if ``--force`` is specified.

    Returns 0 on success, 1 if any warnings encountered.
    """

    after, force = opts.get('after'), opts.get('force')
    if not pats and not after:
        raise error.Abort(_('no files specified'))

    m = scmutil.match(repo[None], pats, opts)
    subrepos = opts.get('subrepos')
    return cmdutil.remove(ui, repo, m, "", after, force, subrepos)

@command('rename|move|mv',
    [('A', 'after', None, _('record a rename that has already occurred')),
    ('f', 'force', None, _('forcibly copy over an existing managed file')),
    ] + walkopts + dryrunopts,
    _('[OPTION]... SOURCE... DEST'))
def rename(ui, repo, *pats, **opts):
    """rename files; equivalent of copy + remove

    Mark dest as copies of sources; mark sources for deletion. If dest
    is a directory, copies are put in that directory. If dest is a
    file, there can only be one source.

    By default, this command copies the contents of files as they
    exist in the working directory. If invoked with -A/--after, the
    operation is recorded, but no copying is performed.

    This command takes effect at the next commit. To undo a rename
    before that, see :hg:`revert`.

    Returns 0 on success, 1 if errors are encountered.
    """
    with repo.wlock(False):
        return cmdutil.copy(ui, repo, pats, opts, rename=True)

@command('resolve',
    [('a', 'all', None, _('select all unresolved files')),
    ('l', 'list', None, _('list state of files needing merge')),
    ('m', 'mark', None, _('mark files as resolved')),
    ('u', 'unmark', None, _('mark files as unresolved')),
    ('n', 'no-status', None, _('hide status prefix'))]
    + mergetoolopts + walkopts + formatteropts,
    _('[OPTION]... [FILE]...'),
    inferrepo=True)
def resolve(ui, repo, *pats, **opts):
    """redo merges or set/view the merge status of files

    Merges with unresolved conflicts are often the result of
    non-interactive merging using the ``internal:merge`` configuration
    setting, or a command-line merge tool like ``diff3``. The resolve
    command is used to manage the files involved in a merge, after
    :hg:`merge` has been run, and before :hg:`commit` is run (i.e. the
    working directory must have two parents). See :hg:`help
    merge-tools` for information on configuring merge tools.

    The resolve command can be used in the following ways:

    - :hg:`resolve [--tool TOOL] FILE...`: attempt to re-merge the specified
      files, discarding any previous merge attempts. Re-merging is not
      performed for files already marked as resolved. Use ``--all/-a``
      to select all unresolved files. ``--tool`` can be used to specify
      the merge tool used for the given files. It overrides the HGMERGE
      environment variable and your configuration files.  Previous file
      contents are saved with a ``.orig`` suffix.

    - :hg:`resolve -m [FILE]`: mark a file as having been resolved
      (e.g. after having manually fixed-up the files). The default is
      to mark all unresolved files.

    - :hg:`resolve -u [FILE]...`: mark a file as unresolved. The
      default is to mark all resolved files.

    - :hg:`resolve -l`: list files which had or still have conflicts.
      In the printed list, ``U`` = unresolved and ``R`` = resolved.

    .. note::

       Mercurial will not let you commit files with unresolved merge
       conflicts. You must use :hg:`resolve -m ...` before you can
       commit after a conflicting merge.

    Returns 0 on success, 1 if any files fail a resolve attempt.
    """

    flaglist = 'all mark unmark list no_status'.split()
    all, mark, unmark, show, nostatus = \
        [opts.get(o) for o in flaglist]

    if (show and (mark or unmark)) or (mark and unmark):
        raise error.Abort(_("too many options specified"))
    if pats and all:
        raise error.Abort(_("can't specify --all and patterns"))
    if not (all or pats or show or mark or unmark):
        raise error.Abort(_('no files or directories specified'),
                         hint=('use --all to re-merge all unresolved files'))

    if show:
        fm = ui.formatter('resolve', opts)
        ms = mergemod.mergestate.read(repo)
        m = scmutil.match(repo[None], pats, opts)
        for f in ms:
            if not m(f):
                continue
            l = 'resolve.' + {'u': 'unresolved', 'r': 'resolved',
                              'd': 'driverresolved'}[ms[f]]
            fm.startitem()
            fm.condwrite(not nostatus, 'status', '%s ', ms[f].upper(), label=l)
            fm.write('path', '%s\n', f, label=l)
        fm.end()
        return 0

    with repo.wlock():
        ms = mergemod.mergestate.read(repo)

        if not (ms.active() or repo.dirstate.p2() != nullid):
            raise error.Abort(
                _('resolve command not applicable when not merging'))

        wctx = repo[None]

        if ms.mergedriver and ms.mdstate() == 'u':
            proceed = mergemod.driverpreprocess(repo, ms, wctx)
            ms.commit()
            # allow mark and unmark to go through
            if not mark and not unmark and not proceed:
                return 1

        m = scmutil.match(wctx, pats, opts)
        ret = 0
        didwork = False
        runconclude = False

        tocomplete = []
        for f in ms:
            if not m(f):
                continue

            didwork = True

            # don't let driver-resolved files be marked, and run the conclude
            # step if asked to resolve
            if ms[f] == "d":
                exact = m.exact(f)
                if mark:
                    if exact:
                        ui.warn(_('not marking %s as it is driver-resolved\n')
                                % f)
                elif unmark:
                    if exact:
                        ui.warn(_('not unmarking %s as it is driver-resolved\n')
                                % f)
                else:
                    runconclude = True
                continue

            if mark:
                ms.mark(f, "r")
            elif unmark:
                ms.mark(f, "u")
            else:
                # backup pre-resolve (merge uses .orig for its own purposes)
                a = repo.wjoin(f)
                try:
                    util.copyfile(a, a + ".resolve")
                except (IOError, OSError) as inst:
                    if inst.errno != errno.ENOENT:
                        raise

                try:
                    # preresolve file
                    ui.setconfig('ui', 'forcemerge', opts.get('tool', ''),
                                 'resolve')
                    complete, r = ms.preresolve(f, wctx)
                    if not complete:
                        tocomplete.append(f)
                    elif r:
                        ret = 1
                finally:
                    ui.setconfig('ui', 'forcemerge', '', 'resolve')
                    ms.commit()

                # replace filemerge's .orig file with our resolve file, but only
                # for merges that are complete
                if complete:
                    try:
                        util.rename(a + ".resolve",
                                    scmutil.origpath(ui, repo, a))
                    except OSError as inst:
                        if inst.errno != errno.ENOENT:
                            raise

        for f in tocomplete:
            try:
                # resolve file
                ui.setconfig('ui', 'forcemerge', opts.get('tool', ''),
                             'resolve')
                r = ms.resolve(f, wctx)
                if r:
                    ret = 1
            finally:
                ui.setconfig('ui', 'forcemerge', '', 'resolve')
                ms.commit()

            # replace filemerge's .orig file with our resolve file
            a = repo.wjoin(f)
            try:
                util.rename(a + ".resolve", scmutil.origpath(ui, repo, a))
            except OSError as inst:
                if inst.errno != errno.ENOENT:
                    raise

        ms.commit()
        ms.recordactions()

        if not didwork and pats:
            hint = None
            if not any([p for p in pats if p.find(':') >= 0]):
                pats = ['path:%s' % p for p in pats]
                m = scmutil.match(wctx, pats, opts)
                for f in ms:
                    if not m(f):
                        continue
                    flags = ''.join(['-%s ' % o[0] for o in flaglist
                                                   if opts.get(o)])
                    hint = _("(try: hg resolve %s%s)\n") % (
                             flags,
                             ' '.join(pats))
                    break
            ui.warn(_("arguments do not match paths that need resolving\n"))
            if hint:
                ui.warn(hint)
        elif ms.mergedriver and ms.mdstate() != 's':
            # run conclude step when either a driver-resolved file is requested
            # or there are no driver-resolved files
            # we can't use 'ret' to determine whether any files are unresolved
            # because we might not have tried to resolve some
            if ((runconclude or not list(ms.driverresolved()))
                and not list(ms.unresolved())):
                proceed = mergemod.driverconclude(repo, ms, wctx)
                ms.commit()
                if not proceed:
                    return 1

    # Nudge users into finishing an unfinished operation
    unresolvedf = list(ms.unresolved())
    driverresolvedf = list(ms.driverresolved())
    if not unresolvedf and not driverresolvedf:
        ui.status(_('(no more unresolved files)\n'))
        cmdutil.checkafterresolved(repo)
    elif not unresolvedf:
        ui.status(_('(no more unresolved files -- '
                    'run "hg resolve --all" to conclude)\n'))

    return ret

@command('revert',
    [('a', 'all', None, _('revert all changes when no arguments given')),
    ('d', 'date', '', _('tipmost revision matching date'), _('DATE')),
    ('r', 'rev', '', _('revert to the specified revision'), _('REV')),
    ('C', 'no-backup', None, _('do not save backup copies of files')),
    ('i', 'interactive', None,
            _('interactively select the changes (EXPERIMENTAL)')),
    ] + walkopts + dryrunopts,
    _('[OPTION]... [-r REV] [NAME]...'))
def revert(ui, repo, *pats, **opts):
    """restore files to their checkout state

    .. note::

       To check out earlier revisions, you should use :hg:`update REV`.
       To cancel an uncommitted merge (and lose your changes),
       use :hg:`update --clean .`.

    With no revision specified, revert the specified files or directories
    to the contents they had in the parent of the working directory.
    This restores the contents of files to an unmodified
    state and unschedules adds, removes, copies, and renames. If the
    working directory has two parents, you must explicitly specify a
    revision.

    Using the -r/--rev or -d/--date options, revert the given files or
    directories to their states as of a specific revision. Because
    revert does not change the working directory parents, this will
    cause these files to appear modified. This can be helpful to "back
    out" some or all of an earlier change. See :hg:`backout` for a
    related method.

    Modified files are saved with a .orig suffix before reverting.
    To disable these backups, use --no-backup. It is possible to store
    the backup files in a custom directory relative to the root of the
    repository by setting the ``ui.origbackuppath`` configuration
    option.

    See :hg:`help dates` for a list of formats valid for -d/--date.

    See :hg:`help backout` for a way to reverse the effect of an
    earlier changeset.

    Returns 0 on success.
    """

    if opts.get("date"):
        if opts.get("rev"):
            raise error.Abort(_("you can't specify a revision and a date"))
        opts["rev"] = cmdutil.finddate(ui, repo, opts["date"])

    parent, p2 = repo.dirstate.parents()
    if not opts.get('rev') and p2 != nullid:
        # revert after merge is a trap for new users (issue2915)
        raise error.Abort(_('uncommitted merge with no revision specified'),
                         hint=_("use 'hg update' or see 'hg help revert'"))

    ctx = scmutil.revsingle(repo, opts.get('rev'))

    if (not (pats or opts.get('include') or opts.get('exclude') or
             opts.get('all') or opts.get('interactive'))):
        msg = _("no files or directories specified")
        if p2 != nullid:
            hint = _("uncommitted merge, use --all to discard all changes,"
                     " or 'hg update -C .' to abort the merge")
            raise error.Abort(msg, hint=hint)
        dirty = any(repo.status())
        node = ctx.node()
        if node != parent:
            if dirty:
                hint = _("uncommitted changes, use --all to discard all"
                         " changes, or 'hg update %s' to update") % ctx.rev()
            else:
                hint = _("use --all to revert all files,"
                         " or 'hg update %s' to update") % ctx.rev()
        elif dirty:
            hint = _("uncommitted changes, use --all to discard all changes")
        else:
            hint = _("use --all to revert all files")
        raise error.Abort(msg, hint=hint)

    return cmdutil.revert(ui, repo, ctx, (parent, p2), *pats, **opts)

@command('rollback', dryrunopts +
         [('f', 'force', False, _('ignore safety measures'))])
def rollback(ui, repo, **opts):
    """roll back the last transaction (DANGEROUS) (DEPRECATED)

    Please use :hg:`commit --amend` instead of rollback to correct
    mistakes in the last commit.

    This command should be used with care. There is only one level of
    rollback, and there is no way to undo a rollback. It will also
    restore the dirstate at the time of the last transaction, losing
    any dirstate changes since that time. This command does not alter
    the working directory.

    Transactions are used to encapsulate the effects of all commands
    that create new changesets or propagate existing changesets into a
    repository.

    .. container:: verbose

      For example, the following commands are transactional, and their
      effects can be rolled back:

      - commit
      - import
      - pull
      - push (with this repository as the destination)
      - unbundle

      To avoid permanent data loss, rollback will refuse to rollback a
      commit transaction if it isn't checked out. Use --force to
      override this protection.

      The rollback command can be entirely disabled by setting the
      ``ui.rollback`` configuration setting to false. If you're here
      because you want to use rollback and it's disabled, you can
      re-enable the command by setting ``ui.rollback`` to true.

    This command is not intended for use on public repositories. Once
    changes are visible for pull by other users, rolling a transaction
    back locally is ineffective (someone else may already have pulled
    the changes). Furthermore, a race is possible with readers of the
    repository; for example an in-progress pull from the repository
    may fail if a rollback is performed.

    Returns 0 on success, 1 if no rollback data is available.
    """
    if not ui.configbool('ui', 'rollback', True):
        raise error.Abort(_('rollback is disabled because it is unsafe'),
                          hint=('see `hg help -v rollback` for information'))
    return repo.rollback(dryrun=opts.get('dry_run'),
                         force=opts.get('force'))

@command('root', [])
def root(ui, repo):
    """print the root (top) of the current working directory

    Print the root directory of the current repository.

    Returns 0 on success.
    """
    ui.write(repo.root + "\n")

@command('^serve',
    [('A', 'accesslog', '', _('name of access log file to write to'),
     _('FILE')),
    ('d', 'daemon', None, _('run server in background')),
    ('', 'daemon-postexec', [], _('used internally by daemon mode')),
    ('E', 'errorlog', '', _('name of error log file to write to'), _('FILE')),
    # use string type, then we can check if something was passed
    ('p', 'port', '', _('port to listen on (default: 8000)'), _('PORT')),
    ('a', 'address', '', _('address to listen on (default: all interfaces)'),
     _('ADDR')),
    ('', 'prefix', '', _('prefix path to serve from (default: server root)'),
     _('PREFIX')),
    ('n', 'name', '',
     _('name to show in web pages (default: working directory)'), _('NAME')),
    ('', 'web-conf', '',
     _("name of the hgweb config file (see 'hg help hgweb')"), _('FILE')),
    ('', 'webdir-conf', '', _('name of the hgweb config file (DEPRECATED)'),
     _('FILE')),
    ('', 'pid-file', '', _('name of file to write process ID to'), _('FILE')),
    ('', 'stdio', None, _('for remote clients')),
    ('', 'cmdserver', '', _('for remote clients'), _('MODE')),
    ('t', 'templates', '', _('web templates to use'), _('TEMPLATE')),
    ('', 'style', '', _('template style to use'), _('STYLE')),
    ('6', 'ipv6', None, _('use IPv6 in addition to IPv4')),
    ('', 'certificate', '', _('SSL certificate file'), _('FILE'))],
    _('[OPTION]...'),
    optionalrepo=True)
def serve(ui, repo, **opts):
    """start stand-alone webserver

    Start a local HTTP repository browser and pull server. You can use
    this for ad-hoc sharing and browsing of repositories. It is
    recommended to use a real web server to serve a repository for
    longer periods of time.

    Please note that the server does not implement access control.
    This means that, by default, anybody can read from the server and
    nobody can write to it by default. Set the ``web.allow_push``
    option to ``*`` to allow everybody to push to the server. You
    should use a real web server if you need to authenticate users.

    By default, the server logs accesses to stdout and errors to
    stderr. Use the -A/--accesslog and -E/--errorlog options to log to
    files.

    To have the server choose a free port number to listen on, specify
    a port number of 0; in this case, the server will print the port
    number it uses.

    Returns 0 on success.
    """

    if opts["stdio"] and opts["cmdserver"]:
        raise error.Abort(_("cannot use --stdio with --cmdserver"))

    if opts["stdio"]:
        if repo is None:
            raise error.RepoError(_("there is no Mercurial repository here"
                                    " (.hg not found)"))
        s = sshserver.sshserver(ui, repo)
        s.serve_forever()

    if opts["cmdserver"]:
        service = commandserver.createservice(ui, repo, opts)
    else:
        service = hgweb.createservice(ui, repo, opts)
    return cmdutil.service(opts, initfn=service.init, runfn=service.run)

@command('^status|st',
    [('A', 'all', None, _('show status of all files')),
    ('m', 'modified', None, _('show only modified files')),
    ('a', 'added', None, _('show only added files')),
    ('r', 'removed', None, _('show only removed files')),
    ('d', 'deleted', None, _('show only deleted (but tracked) files')),
    ('c', 'clean', None, _('show only files without changes')),
    ('u', 'unknown', None, _('show only unknown (not tracked) files')),
    ('i', 'ignored', None, _('show only ignored files')),
    ('n', 'no-status', None, _('hide status prefix')),
    ('C', 'copies', None, _('show source of copied files')),
    ('0', 'print0', None, _('end filenames with NUL, for use with xargs')),
    ('', 'rev', [], _('show difference from revision'), _('REV')),
    ('', 'change', '', _('list the changed files of a revision'), _('REV')),
    ] + walkopts + subrepoopts + formatteropts,
    _('[OPTION]... [FILE]...'),
    inferrepo=True)
def status(ui, repo, *pats, **opts):
    """show changed files in the working directory

    Show status of files in the repository. If names are given, only
    files that match are shown. Files that are clean or ignored or
    the source of a copy/move operation, are not listed unless
    -c/--clean, -i/--ignored, -C/--copies or -A/--all are given.
    Unless options described with "show only ..." are given, the
    options -mardu are used.

    Option -q/--quiet hides untracked (unknown and ignored) files
    unless explicitly requested with -u/--unknown or -i/--ignored.

    .. note::

       :hg:`status` may appear to disagree with diff if permissions have
       changed or a merge has occurred. The standard diff format does
       not report permission changes and diff only reports changes
       relative to one merge parent.

    If one revision is given, it is used as the base revision.
    If two revisions are given, the differences between them are
    shown. The --change option can also be used as a shortcut to list
    the changed files of a revision from its first parent.

    The codes used to show the status of files are::

      M = modified
      A = added
      R = removed
      C = clean
      ! = missing (deleted by non-hg command, but still tracked)
      ? = not tracked
      I = ignored
        = origin of the previous file (with --copies)

    .. container:: verbose

      Examples:

      - show changes in the working directory relative to a
        changeset::

          hg status --rev 9353

      - show changes in the working directory relative to the
        current directory (see :hg:`help patterns` for more information)::

          hg status re:

      - show all changes including copies in an existing changeset::

          hg status --copies --change 9353

      - get a NUL separated list of added files, suitable for xargs::

          hg status -an0

    Returns 0 on success.
    """

    revs = opts.get('rev')
    change = opts.get('change')

    if revs and change:
        msg = _('cannot specify --rev and --change at the same time')
        raise error.Abort(msg)
    elif change:
        node2 = scmutil.revsingle(repo, change, None).node()
        node1 = repo[node2].p1().node()
    else:
        node1, node2 = scmutil.revpair(repo, revs)

    if pats:
        cwd = repo.getcwd()
    else:
        cwd = ''

    if opts.get('print0'):
        end = '\0'
    else:
        end = '\n'
    copy = {}
    states = 'modified added removed deleted unknown ignored clean'.split()
    show = [k for k in states if opts.get(k)]
    if opts.get('all'):
        show += ui.quiet and (states[:4] + ['clean']) or states
    if not show:
        if ui.quiet:
            show = states[:4]
        else:
            show = states[:5]

    m = scmutil.match(repo[node2], pats, opts)
    stat = repo.status(node1, node2, m,
                       'ignored' in show, 'clean' in show, 'unknown' in show,
                       opts.get('subrepos'))
    changestates = zip(states, 'MAR!?IC', stat)

    if (opts.get('all') or opts.get('copies')
        or ui.configbool('ui', 'statuscopies')) and not opts.get('no_status'):
        copy = copies.pathcopies(repo[node1], repo[node2], m)

    fm = ui.formatter('status', opts)
    fmt = '%s' + end
    showchar = not opts.get('no_status')

    for state, char, files in changestates:
        if state in show:
            label = 'status.' + state
            for f in files:
                fm.startitem()
                fm.condwrite(showchar, 'status', '%s ', char, label=label)
                fm.write('path', fmt, repo.pathto(f, cwd), label=label)
                if f in copy:
                    fm.write("copy", '  %s' + end, repo.pathto(copy[f], cwd),
                             label='status.copied')
    fm.end()

@command('^summary|sum',
    [('', 'remote', None, _('check for push and pull'))], '[--remote]')
def summary(ui, repo, **opts):
    """summarize working directory state

    This generates a brief summary of the working directory state,
    including parents, branch, commit status, phase and available updates.

    With the --remote option, this will check the default paths for
    incoming and outgoing changes. This can be time-consuming.

    Returns 0 on success.
    """

    ctx = repo[None]
    parents = ctx.parents()
    pnode = parents[0].node()
    marks = []

    ms = None
    try:
        ms = mergemod.mergestate.read(repo)
    except error.UnsupportedMergeRecords as e:
        s = ' '.join(e.recordtypes)
        ui.warn(
            _('warning: merge state has unsupported record types: %s\n') % s)
        unresolved = 0
    else:
        unresolved = [f for f in ms if ms[f] == 'u']

    for p in parents:
        # label with log.changeset (instead of log.parent) since this
        # shows a working directory parent *changeset*:
        # i18n: column positioning for "hg summary"
        ui.write(_('parent: %d:%s ') % (p.rev(), str(p)),
                 label='log.changeset changeset.%s' % p.phasestr())
        ui.write(' '.join(p.tags()), label='log.tag')
        if p.bookmarks():
            marks.extend(p.bookmarks())
        if p.rev() == -1:
            if not len(repo):
                ui.write(_(' (empty repository)'))
            else:
                ui.write(_(' (no revision checked out)'))
        ui.write('\n')
        if p.description():
            ui.status(' ' + p.description().splitlines()[0].strip() + '\n',
                      label='log.summary')

    branch = ctx.branch()
    bheads = repo.branchheads(branch)
    # i18n: column positioning for "hg summary"
    m = _('branch: %s\n') % branch
    if branch != 'default':
        ui.write(m, label='log.branch')
    else:
        ui.status(m, label='log.branch')

    if marks:
        active = repo._activebookmark
        # i18n: column positioning for "hg summary"
        ui.write(_('bookmarks:'), label='log.bookmark')
        if active is not None:
            if active in marks:
                ui.write(' *' + active, label=activebookmarklabel)
                marks.remove(active)
            else:
                ui.write(' [%s]' % active, label=activebookmarklabel)
        for m in marks:
            ui.write(' ' + m, label='log.bookmark')
        ui.write('\n', label='log.bookmark')

    status = repo.status(unknown=True)

    c = repo.dirstate.copies()
    copied, renamed = [], []
    for d, s in c.iteritems():
        if s in status.removed:
            status.removed.remove(s)
            renamed.append(d)
        else:
            copied.append(d)
        if d in status.added:
            status.added.remove(d)

    subs = [s for s in ctx.substate if ctx.sub(s).dirty()]

    labels = [(ui.label(_('%d modified'), 'status.modified'), status.modified),
              (ui.label(_('%d added'), 'status.added'), status.added),
              (ui.label(_('%d removed'), 'status.removed'), status.removed),
              (ui.label(_('%d renamed'), 'status.copied'), renamed),
              (ui.label(_('%d copied'), 'status.copied'), copied),
              (ui.label(_('%d deleted'), 'status.deleted'), status.deleted),
              (ui.label(_('%d unknown'), 'status.unknown'), status.unknown),
              (ui.label(_('%d unresolved'), 'resolve.unresolved'), unresolved),
              (ui.label(_('%d subrepos'), 'status.modified'), subs)]
    t = []
    for l, s in labels:
        if s:
            t.append(l % len(s))

    t = ', '.join(t)
    cleanworkdir = False

    if repo.vfs.exists('graftstate'):
        t += _(' (graft in progress)')
    if repo.vfs.exists('updatestate'):
        t += _(' (interrupted update)')
    elif len(parents) > 1:
        t += _(' (merge)')
    elif branch != parents[0].branch():
        t += _(' (new branch)')
    elif (parents[0].closesbranch() and
          pnode in repo.branchheads(branch, closed=True)):
        t += _(' (head closed)')
    elif not (status.modified or status.added or status.removed or renamed or
              copied or subs):
        t += _(' (clean)')
        cleanworkdir = True
    elif pnode not in bheads:
        t += _(' (new branch head)')

    if parents:
        pendingphase = max(p.phase() for p in parents)
    else:
        pendingphase = phases.public

    if pendingphase > phases.newcommitphase(ui):
        t += ' (%s)' % phases.phasenames[pendingphase]

    if cleanworkdir:
        # i18n: column positioning for "hg summary"
        ui.status(_('commit: %s\n') % t.strip())
    else:
        # i18n: column positioning for "hg summary"
        ui.write(_('commit: %s\n') % t.strip())

    # all ancestors of branch heads - all ancestors of parent = new csets
    new = len(repo.changelog.findmissing([pctx.node() for pctx in parents],
                                         bheads))

    if new == 0:
        # i18n: column positioning for "hg summary"
        ui.status(_('update: (current)\n'))
    elif pnode not in bheads:
        # i18n: column positioning for "hg summary"
        ui.write(_('update: %d new changesets (update)\n') % new)
    else:
        # i18n: column positioning for "hg summary"
        ui.write(_('update: %d new changesets, %d branch heads (merge)\n') %
                 (new, len(bheads)))

    t = []
    draft = len(repo.revs('draft()'))
    if draft:
        t.append(_('%d draft') % draft)
    secret = len(repo.revs('secret()'))
    if secret:
        t.append(_('%d secret') % secret)

    if draft or secret:
        ui.status(_('phases: %s\n') % ', '.join(t))

    if obsolete.isenabled(repo, obsolete.createmarkersopt):
        for trouble in ("unstable", "divergent", "bumped"):
            numtrouble = len(repo.revs(trouble + "()"))
            # We write all the possibilities to ease translation
            troublemsg = {
               "unstable": _("unstable: %d changesets"),
               "divergent": _("divergent: %d changesets"),
               "bumped": _("bumped: %d changesets"),
            }
            if numtrouble > 0:
                ui.status(troublemsg[trouble] % numtrouble + "\n")

    cmdutil.summaryhooks(ui, repo)

    if opts.get('remote'):
        needsincoming, needsoutgoing = True, True
    else:
        needsincoming, needsoutgoing = False, False
        for i, o in cmdutil.summaryremotehooks(ui, repo, opts, None):
            if i:
                needsincoming = True
            if o:
                needsoutgoing = True
        if not needsincoming and not needsoutgoing:
            return

    def getincoming():
        source, branches = hg.parseurl(ui.expandpath('default'))
        sbranch = branches[0]
        try:
            other = hg.peer(repo, {}, source)
        except error.RepoError:
            if opts.get('remote'):
                raise
            return source, sbranch, None, None, None
        revs, checkout = hg.addbranchrevs(repo, other, branches, None)
        if revs:
            revs = [other.lookup(rev) for rev in revs]
        ui.debug('comparing with %s\n' % util.hidepassword(source))
        repo.ui.pushbuffer()
        commoninc = discovery.findcommonincoming(repo, other, heads=revs)
        repo.ui.popbuffer()
        return source, sbranch, other, commoninc, commoninc[1]

    if needsincoming:
        source, sbranch, sother, commoninc, incoming = getincoming()
    else:
        source = sbranch = sother = commoninc = incoming = None

    def getoutgoing():
        dest, branches = hg.parseurl(ui.expandpath('default-push', 'default'))
        dbranch = branches[0]
        revs, checkout = hg.addbranchrevs(repo, repo, branches, None)
        if source != dest:
            try:
                dother = hg.peer(repo, {}, dest)
            except error.RepoError:
                if opts.get('remote'):
                    raise
                return dest, dbranch, None, None
            ui.debug('comparing with %s\n' % util.hidepassword(dest))
        elif sother is None:
            # there is no explicit destination peer, but source one is invalid
            return dest, dbranch, None, None
        else:
            dother = sother
        if (source != dest or (sbranch is not None and sbranch != dbranch)):
            common = None
        else:
            common = commoninc
        if revs:
            revs = [repo.lookup(rev) for rev in revs]
        repo.ui.pushbuffer()
        outgoing = discovery.findcommonoutgoing(repo, dother, onlyheads=revs,
                                                commoninc=common)
        repo.ui.popbuffer()
        return dest, dbranch, dother, outgoing

    if needsoutgoing:
        dest, dbranch, dother, outgoing = getoutgoing()
    else:
        dest = dbranch = dother = outgoing = None

    if opts.get('remote'):
        t = []
        if incoming:
            t.append(_('1 or more incoming'))
        o = outgoing.missing
        if o:
            t.append(_('%d outgoing') % len(o))
        other = dother or sother
        if 'bookmarks' in other.listkeys('namespaces'):
            counts = bookmarks.summary(repo, other)
            if counts[0] > 0:
                t.append(_('%d incoming bookmarks') % counts[0])
            if counts[1] > 0:
                t.append(_('%d outgoing bookmarks') % counts[1])

        if t:
            # i18n: column positioning for "hg summary"
            ui.write(_('remote: %s\n') % (', '.join(t)))
        else:
            # i18n: column positioning for "hg summary"
            ui.status(_('remote: (synced)\n'))

    cmdutil.summaryremotehooks(ui, repo, opts,
                               ((source, sbranch, sother, commoninc),
                                (dest, dbranch, dother, outgoing)))

@command('tag',
    [('f', 'force', None, _('force tag')),
    ('l', 'local', None, _('make the tag local')),
    ('r', 'rev', '', _('revision to tag'), _('REV')),
    ('', 'remove', None, _('remove a tag')),
    # -l/--local is already there, commitopts cannot be used
    ('e', 'edit', None, _('invoke editor on commit messages')),
    ('m', 'message', '', _('use text as commit message'), _('TEXT')),
    ] + commitopts2,
    _('[-f] [-l] [-m TEXT] [-d DATE] [-u USER] [-r REV] NAME...'))
def tag(ui, repo, name1, *names, **opts):
    """add one or more tags for the current or given revision

    Name a particular revision using <name>.

    Tags are used to name particular revisions of the repository and are
    very useful to compare different revisions, to go back to significant
    earlier versions or to mark branch points as releases, etc. Changing
    an existing tag is normally disallowed; use -f/--force to override.

    If no revision is given, the parent of the working directory is
    used.

    To facilitate version control, distribution, and merging of tags,
    they are stored as a file named ".hgtags" which is managed similarly
    to other project files and can be hand-edited if necessary. This
    also means that tagging creates a new commit. The file
    ".hg/localtags" is used for local tags (not shared among
    repositories).

    Tag commits are usually made at the head of a branch. If the parent
    of the working directory is not a branch head, :hg:`tag` aborts; use
    -f/--force to force the tag commit to be based on a non-head
    changeset.

    See :hg:`help dates` for a list of formats valid for -d/--date.

    Since tag names have priority over branch names during revision
    lookup, using an existing branch name as a tag name is discouraged.

    Returns 0 on success.
    """
    wlock = lock = None
    try:
        wlock = repo.wlock()
        lock = repo.lock()
        rev_ = "."
        names = [t.strip() for t in (name1,) + names]
        if len(names) != len(set(names)):
            raise error.Abort(_('tag names must be unique'))
        for n in names:
            scmutil.checknewlabel(repo, n, 'tag')
            if not n:
                raise error.Abort(_('tag names cannot consist entirely of '
                                   'whitespace'))
        if opts.get('rev') and opts.get('remove'):
            raise error.Abort(_("--rev and --remove are incompatible"))
        if opts.get('rev'):
            rev_ = opts['rev']
        message = opts.get('message')
        if opts.get('remove'):
            if opts.get('local'):
                expectedtype = 'local'
            else:
                expectedtype = 'global'

            for n in names:
                if not repo.tagtype(n):
                    raise error.Abort(_("tag '%s' does not exist") % n)
                if repo.tagtype(n) != expectedtype:
                    if expectedtype == 'global':
                        raise error.Abort(_("tag '%s' is not a global tag") % n)
                    else:
                        raise error.Abort(_("tag '%s' is not a local tag") % n)
            rev_ = 'null'
            if not message:
                # we don't translate commit messages
                message = 'Removed tag %s' % ', '.join(names)
        elif not opts.get('force'):
            for n in names:
                if n in repo.tags():
                    raise error.Abort(_("tag '%s' already exists "
                                       "(use -f to force)") % n)
        if not opts.get('local'):
            p1, p2 = repo.dirstate.parents()
            if p2 != nullid:
                raise error.Abort(_('uncommitted merge'))
            bheads = repo.branchheads()
            if not opts.get('force') and bheads and p1 not in bheads:
                raise error.Abort(_('working directory is not at a branch head '
                                    '(use -f to force)'))
        r = scmutil.revsingle(repo, rev_).node()

        if not message:
            # we don't translate commit messages
            message = ('Added tag %s for changeset %s' %
                       (', '.join(names), short(r)))

        date = opts.get('date')
        if date:
            date = util.parsedate(date)

        if opts.get('remove'):
            editform = 'tag.remove'
        else:
            editform = 'tag.add'
        editor = cmdutil.getcommiteditor(editform=editform, **opts)

        # don't allow tagging the null rev
        if (not opts.get('remove') and
            scmutil.revsingle(repo, rev_).rev() == nullrev):
            raise error.Abort(_("cannot tag null revision"))

        repo.tag(names, r, message, opts.get('local'), opts.get('user'), date,
                 editor=editor)
    finally:
        release(lock, wlock)

@command('tags', formatteropts, '')
def tags(ui, repo, **opts):
    """list repository tags

    This lists both regular and local tags. When the -v/--verbose
    switch is used, a third column "local" is printed for local tags.
    When the -q/--quiet switch is used, only the tag name is printed.

    Returns 0 on success.
    """

    fm = ui.formatter('tags', opts)
    hexfunc = fm.hexfunc
    tagtype = ""

    for t, n in reversed(repo.tagslist()):
        hn = hexfunc(n)
        label = 'tags.normal'
        tagtype = ''
        if repo.tagtype(t) == 'local':
            label = 'tags.local'
            tagtype = 'local'

        fm.startitem()
        fm.write('tag', '%s', t, label=label)
        fmt = " " * (30 - encoding.colwidth(t)) + ' %5d:%s'
        fm.condwrite(not ui.quiet, 'rev node', fmt,
                     repo.changelog.rev(n), hn, label=label)
        fm.condwrite(ui.verbose and tagtype, 'type', ' %s',
                     tagtype, label=label)
        fm.plain('\n')
    fm.end()

@command('tip',
    [('p', 'patch', None, _('show patch')),
    ('g', 'git', None, _('use git extended diff format')),
    ] + templateopts,
    _('[-p] [-g]'))
def tip(ui, repo, **opts):
    """show the tip revision (DEPRECATED)

    The tip revision (usually just called the tip) is the changeset
    most recently added to the repository (and therefore the most
    recently changed head).

    If you have just made a commit, that commit will be the tip. If
    you have just pulled changes from another repository, the tip of
    that repository becomes the current tip. The "tip" tag is special
    and cannot be renamed or assigned to a different changeset.

    This command is deprecated, please use :hg:`heads` instead.

    Returns 0 on success.
    """
    displayer = cmdutil.show_changeset(ui, repo, opts)
    displayer.show(repo['tip'])
    displayer.close()

@command('unbundle',
    [('u', 'update', None,
     _('update to new branch head if changesets were unbundled'))],
    _('[-u] FILE...'))
def unbundle(ui, repo, fname1, *fnames, **opts):
    """apply one or more changegroup files

    Apply one or more compressed changegroup files generated by the
    bundle command.

    Returns 0 on success, 1 if an update has unresolved files.
    """
    fnames = (fname1,) + fnames

    with repo.lock():
        for fname in fnames:
            f = hg.openpath(ui, fname)
            gen = exchange.readbundle(ui, f, fname)
            if isinstance(gen, bundle2.unbundle20):
                tr = repo.transaction('unbundle')
                try:
                    op = bundle2.applybundle(repo, gen, tr, source='unbundle',
                                             url='bundle:' + fname)
                    tr.close()
                except error.BundleUnknownFeatureError as exc:
                    raise error.Abort(_('%s: unknown bundle feature, %s')
                                      % (fname, exc),
                                      hint=_("see https://mercurial-scm.org/"
                                             "wiki/BundleFeature for more "
                                             "information"))
                finally:
                    if tr:
                        tr.release()
                changes = [r.get('return', 0)
                           for r in op.records['changegroup']]
                modheads = changegroup.combineresults(changes)
            elif isinstance(gen, streamclone.streamcloneapplier):
                raise error.Abort(
                        _('packed bundles cannot be applied with '
                          '"hg unbundle"'),
                        hint=_('use "hg debugapplystreamclonebundle"'))
            else:
                modheads = gen.apply(repo, 'unbundle', 'bundle:' + fname)

    return postincoming(ui, repo, modheads, opts.get('update'), None, None)

@command('^update|up|checkout|co',
    [('C', 'clean', None, _('discard uncommitted changes (no backup)')),
    ('c', 'check', None, _('require clean working directory')),
    ('d', 'date', '', _('tipmost revision matching date'), _('DATE')),
    ('r', 'rev', '', _('revision'), _('REV'))
     ] + mergetoolopts,
    _('[-c] [-C] [-d DATE] [[-r] REV]'))
def update(ui, repo, node=None, rev=None, clean=False, date=None, check=False,
           tool=None):
    """update working directory (or switch revisions)

    Update the repository's working directory to the specified
    changeset. If no changeset is specified, update to the tip of the
    current named branch and move the active bookmark (see :hg:`help
    bookmarks`).

    Update sets the working directory's parent revision to the specified
    changeset (see :hg:`help parents`).

    If the changeset is not a descendant or ancestor of the working
    directory's parent, the update is aborted. With the -c/--check
    option, the working directory is checked for uncommitted changes; if
    none are found, the working directory is updated to the specified
    changeset.

    .. container:: verbose

      The following rules apply when the working directory contains
      uncommitted changes:

      1. If neither -c/--check nor -C/--clean is specified, and if
         the requested changeset is an ancestor or descendant of
         the working directory's parent, the uncommitted changes
         are merged into the requested changeset and the merged
         result is left uncommitted. If the requested changeset is
         not an ancestor or descendant (that is, it is on another
         branch), the update is aborted and the uncommitted changes
         are preserved.

      2. With the -c/--check option, the update is aborted and the
         uncommitted changes are preserved.

      3. With the -C/--clean option, uncommitted changes are discarded and
         the working directory is updated to the requested changeset.

    To cancel an uncommitted merge (and lose your changes), use
    :hg:`update --clean .`.

    Use null as the changeset to remove the working directory (like
    :hg:`clone -U`).

    If you want to revert just one file to an older revision, use
    :hg:`revert [-r REV] NAME`.

    See :hg:`help dates` for a list of formats valid for -d/--date.

    Returns 0 on success, 1 if there are unresolved files.
    """
    if rev and node:
        raise error.Abort(_("please specify just one revision"))

    if rev is None or rev == '':
        rev = node

    if date and rev is not None:
        raise error.Abort(_("you can't specify a revision and a date"))

    if check and clean:
        raise error.Abort(_("cannot specify both -c/--check and -C/--clean"))

    with repo.wlock():
        cmdutil.clearunfinished(repo)

        if date:
            rev = cmdutil.finddate(ui, repo, date)

        # if we defined a bookmark, we have to remember the original name
        brev = rev
        rev = scmutil.revsingle(repo, rev, rev).rev()

        if check:
            cmdutil.bailifchanged(repo, merge=False)

        repo.ui.setconfig('ui', 'forcemerge', tool, 'update')

        return hg.updatetotally(ui, repo, rev, brev, clean=clean, check=check)

@command('verify', [])
def verify(ui, repo):
    """verify the integrity of the repository

    Verify the integrity of the current repository.

    This will perform an extensive check of the repository's
    integrity, validating the hashes and checksums of each entry in
    the changelog, manifest, and tracked files, as well as the
    integrity of their crosslinks and indices.

    Please see https://mercurial-scm.org/wiki/RepositoryCorruption
    for more information about recovery from corruption of the
    repository.

    Returns 0 on success, 1 if errors are encountered.
    """
    return hg.verify(repo)

@command('version', [] + formatteropts, norepo=True)
def version_(ui, **opts):
    """output version and copyright information"""
    fm = ui.formatter("version", opts)
    fm.startitem()
    fm.write("ver", _("Mercurial Distributed SCM (version %s)\n"),
             util.version())
    license = _(
        "(see https://mercurial-scm.org for more information)\n"
        "\nCopyright (C) 2005-2016 Matt Mackall and others\n"
        "This is free software; see the source for copying conditions. "
        "There is NO\nwarranty; "
        "not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.\n"
    )
    if not ui.quiet:
        fm.plain(license)

    if ui.verbose:
        fm.plain(_("\nEnabled extensions:\n\n"))
    # format names and versions into columns
    names = []
    vers = []
    isinternals = []
    for name, module in extensions.extensions():
        names.append(name)
        vers.append(extensions.moduleversion(module) or None)
        isinternals.append(extensions.ismoduleinternal(module))
    fn = fm.nested("extensions")
    if names:
        namefmt = "  %%-%ds  " % max(len(n) for n in names)
        places = [_("external"), _("internal")]
        for n, v, p in zip(names, vers, isinternals):
            fn.startitem()
            fn.condwrite(ui.verbose, "name", namefmt, n)
            if ui.verbose:
                fn.plain("%s  " % places[p])
            fn.data(bundled=p)
            fn.condwrite(ui.verbose and v, "ver", "%s", v)
            if ui.verbose:
                fn.plain("\n")
    fn.end()
    fm.end()

def loadcmdtable(ui, name, cmdtable):
    """Load command functions from specified cmdtable
    """
    overrides = [cmd for cmd in cmdtable if cmd in table]
    if overrides:
        ui.warn(_("extension '%s' overrides commands: %s\n")
                % (name, " ".join(overrides)))
    table.update(cmdtable)
