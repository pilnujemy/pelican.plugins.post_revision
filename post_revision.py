"""Post Revision Plugin for Pelican.

This plugin read the Git commit hitory for each article or page file, and store
the history as a meta data to the article or page object, so that templates can
make use of this information to show post revision history.

When this plugin is installed, the ``article`` and ``page`` object has an extra
meta data named ``history``, which is a list of ``<date, msg>`` tuples in
reverse order by date.
"""
import subprocess
import dateutil

from pelican import signals

Revision = namedtuple('Revision', ['author', 'date', 'msg'], verbose=True)

def generate_post_revision(generator):
  project_root = generator.settings.get('PROJECT_ROOT', None)
  github_url = generator.settings.get('GITHUB_URL', None)
  github_branch = generator.settings.get('GITHUB_BRANCH', 'master')
  if github_url is not None and github_url.endswith('/'):
    github_url = github_url.rstrip('/')

  pages = []
  pages += getattr(generator, 'articles', [])
  pages += getattr(generator, 'pages', [])
  for page in pages:
    path = getattr(page, 'source_path', None)
    if path is None:
      continue
    try:
      output = subprocess.check_output('git log --format="%%an|%%ai|%%s" %s'\
          % (path), shell=True)
      commits = []
      for line in output.split('\n'):
        line = line.strip()
        if len(line) == 0:
          continue
        parts = line.split('|')
        author, date, msg = parts[0], dateutil.parser.parse(parts[1]), '|'.join(parts[2:])
        commits.append(Revision(author, date, msg))
      setattr(page, 'history', commits)

      if github_url is None or project_root is None:
        continue

      relative_path = path.replace(project_root, '')
      if relative_path.startswith('/'):
        relative_path = relative_path.lstrip('/')

      setattr(page, 'github_history_url', '{gh_url}/commits/{branch}/{path}'.format(gh_url=github_url,
                                                                                    branch=github_branch,
                                                                                    path=relative_path))
    except:
      continue


def register():
  signals.article_generator_finalized.connect(generate_post_revision)
  signals.page_generator_finalized.connect(generate_post_revision)
