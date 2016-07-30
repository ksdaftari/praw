"""Provide the Subreddit class."""
from prawcore import Redirect
from six.moves.urllib.parse import urljoin  # pylint: disable=import-error

from ...const import API_PATH
from ..util import stream_generator
from ..listing.generator import ListingGenerator
from ..listing.mixins import SubredditListingMixin
from .base import RedditBase
from .mixins import MessageableMixin
from .wikipage import WikiPage


class Subreddit(RedditBase, MessageableMixin, SubredditListingMixin):
    """A class for Subreddits."""

    STR_FIELD = 'display_name'
    MESSAGE_PREFIX = '#'

    @staticmethod
    def _create_or_update(_reddit, allow_images=None, allow_top=None,
                          collapse_deleted_comments=None,
                          comment_score_hide_mins=None, description=None,
                          domain=None, exclude_modqueue_banned=None,
                          header_hover_text=None, hide_ads=None, lang=None,
                          key_color=None, link_type=None, name=None,
                          over_18=None, public_description=None,
                          public_traffic=None, show_media=None,
                          spam_comments=None, spam_links=None,
                          spam_selfposts=None, sr=None, submit_link_label=None,
                          submit_text=None, submit_text_label=None,
                          subreddit_type=None, suggested_comment_sort=None,
                          title=None, wiki_edit_age=None, wiki_edit_karma=None,
                          wikimode=None):
        """Create a new subreddit.

        :param _reddit: The reddit session.

        :param allow_images: Allow users to upload images using the native
            image hosting. Only applies to link-only subreddits.
        :param allow_top: Allow the subreddit to appear on /r/all as well as
            the default and trending lists.
        :param collapse_deleted_comments: Collapse deleted and removed comments
            on comments pages by default.
        :param comment_score_hide_mins: The number of minutes to hide comment
            scores.
        :param description: Shown in the sidebar of your subreddit.
        :param domain: Undocumented.
        :param exclude_modqueue_banned: Exclude posts by site-wide banned users
            from modqueue/unmoderated.
        :param header_hover_text: The text seen when hovering over the snoo.
        :param hide_ads: Don't show ads within this subreddit. Only applies to
            gold-user only subreddits.
        :param key_color: A 6-digit rgb hex color (e.g. `#AABBCC`), used as a
            thematic color for your subreddit on mobile.
        :param lang: A valid IETF language tag (underscore separated).
        :param link_type: The types of submissions users can make.
            One of ``any``, ``link``, ``self``.
        :param name: The name for the new subreddit. Required during creation.
        :param over_18: Viewers must be over 18 years old.
        :param public_description: Public description blurb. Appears in search
            results and on the landing page for private subreddits.
        :param public_traffic: Make the traffic stats page public.
        :param show_media: Expand media previews on comments pages.
        :param spam_comments: Spam filter strength for comments.
            One of ``low``, ``high``, ``all``.
        :param spam_links: Spam filter strength for links.
            One of ``low``, ``high``, ``all``.
        :param spam_selfposts: Spam filter strength for selfposts.
            One of ``low``, ``high``, ``all``.
        :param sr: The fullname of the subreddit whose settings will be
            updated.
        :param submit_link_label: Custom label for submit link button
            (blank for default).
        :param submit_text: Text to show on submission page.
        :param submit_text_label: Custom label for submit text post button
            (blank for default).
        :param subreddit_type: One of ``gold_restricted``, ``archived``,
            ``restricted``, ``gold_only``, ``employees_only``, ``private``,
            ``public``.
        :param suggested_comment_sort: All comment threads will use this
            sorting method by default. Leave blank, or choose one of
            ``confidence``, ``top``, ``new``, ``controversial``, ``old``,
            ``random``, ``qa``.
        :param title: The title for the new subreddit.
        :param wiki_edit_age: Account age (days) required to edit and create
            wiki pages.
        :param wiki_edit_karma: Subreddit karma required to edit and create
            wiki pages.
        :param wikimode: One of ``disabled``, ``modonly``, ``anyone``.

        Any parameters left `None` will take on a default value assigned by
        the server.

        :returns: The server response body.
        """
        model = {
            'allow_images': allow_images,
            'allow_top': allow_top,
            'collapse_deleted_comments': collapse_deleted_comments,
            'comment_score_hide_mins': comment_score_hide_mins,
            'description': description,
            'domain': domain,
            'exclude_modqueue_banned': exclude_modqueue_banned,
            'header_hover_text': header_hover_text,
            'hide_ads': hide_ads,
            'key_color': key_color,
            'lang': lang,
            'link_type': link_type,
            'name': name,
            'over_18': over_18,
            'public_description': public_description,
            'public_traffic': public_traffic,
            'show_media': show_media,
            'spam_comments': spam_comments,
            'spam_links': spam_links,
            'spam_selfposts': spam_selfposts,
            'sr': sr,
            'submit_link_label': submit_link_label,
            'submit_text': submit_text,
            'submit_text_label': submit_text_label,
            'suggested_comment_sort': suggested_comment_sort,
            'title': title,
            'type': subreddit_type,
            'wiki_edit_age': wiki_edit_age,
            'wiki_edit_karma': wiki_edit_karma,
            'wikimode': wikimode,
        }
        return _reddit.post(API_PATH['site_admin'], data=model)

    def __init__(self, reddit, display_name=None, _data=None):
        """Initialize a Subreddit instance.

        :param reddit: An instance of :class:`~.Reddit`.
        :param display_name: The name of the subreddit.

        """
        if bool(display_name) == bool(_data):
            raise TypeError(
                'Either `display_name` or `_data` must be provided.')
        super(Subreddit, self).__init__(reddit, _data)
        if display_name:
            self.display_name = display_name
        self._path = API_PATH['subreddit'].format(subreddit=self)
        self._prepare_relationships()
        self.flair = SubredditFlair(self)
        self.mod = SubredditModeration(self)
        self.stream = SubredditStream(self)
        self.wiki = SubredditWiki(self)

    def _info_path(self):
        return API_PATH['subreddit_about'].format(subreddit=self)

    def _prepare_relationships(self):
        for relationship in ['banned', 'contributor', 'moderator', 'muted']:
            setattr(self, relationship,
                    SubredditRelationship(self, relationship))

    def random(self):
        """Return a random Submission."""
        from .submission import Submission
        url = API_PATH['subreddit_random'].format(subreddit=self)
        try:
            self._reddit.get(url, params={'unique': self._reddit._next_unique})
        except Redirect as redirect:
            path = redirect.path
        return Submission(self._reddit, url=urljoin(
            self._reddit.config.reddit_url, path))

    def search(self, query, sort='relevance', syntax='cloudsearch',
               time_filter='all', **generator_kwargs):
        """Return a ListingGenerator for items that match ``query``.

        :param query: The query string to search for.
        :param sort: Can be one of: relevance, hot, top, new,
            comments. (default: relevance).
        :param syntax: Can be one of: cloudsearch, lucene, plain
            (default: cloudsearch).
        :param time_filter: Can be one of: all, day, hour, month, week, year
            (default: all).

        For more information on building a search query see:
            https://www.reddit.com/wiki/search

        """
        self.validate_time_filter(time_filter)
        params = generator_kwargs.setdefault('params', {})
        params.update({'q': query, 'restrict_sr': True, 'sort': sort,
                       'syntax': syntax, 't': time_filter})
        url = API_PATH['search'].format(subreddit=self)
        return ListingGenerator(self._reddit, url, **generator_kwargs)

    def submit(self, title, selftext=None, url=None, resubmit=True,
               send_replies=True):
        """Add a submission to the subreddit.

        :param title: The title of the submission.
        :param selftext: The markdown formatted content for a ``text``
            submission.
        :param url: The URL for a ``link`` submission.
        :param resubmit: When False, an error will occur if the URL has already
            been submitted (Default: True).
        :param send_replies: When True, messages will be sent to the submission
            author when comments are made to the submission (Default: True).
        :returns: A :class:`~.Submission` object for the newly created
            submission.

        Either ``selftext`` or ``url`` can be provided, but not both.

        """
        if bool(selftext) == bool(url):
            raise TypeError('Either `selftext` or `url` must be provided.')

        data = {'sr': str(self), 'resubmit': bool(resubmit),
                'sendreplies': bool(send_replies), 'title': title}
        if selftext is not None:
            data.update(kind='self', text=selftext)
        else:
            data.update(kind='link', url=url)
        return self._reddit.post(API_PATH['submit'], data=data)


class SubredditFlair(object):
    """Provide a set of functions to interact with a Subreddit's flair."""

    def __init__(self, subreddit):
        """Create a SubredditFlair instance.

        :param subreddit: The subreddit whose flair to work with.

        """
        self.subreddit = subreddit

    def __iter__(self):
        """Iterate through the Redditors and their associated flair."""
        url = API_PATH['flairlist'].format(subreddit=self.subreddit)
        params = {'unique': self.subreddit._reddit._next_unique}
        for item in ListingGenerator(self.subreddit._reddit, url, None,
                                     params=params):
            yield item

    def delete_all(self):
        """Delete all Redditor flair in the Subreddit.

        :returns: List of dictionaries indicating the success or failure of
            each delete.

        """
        return self.update(x['user'] for x in self)

    def set(self, thing, text='', css_class=''):
        """Set flair for a Redditor or Submission.

        :param thing: An instance of Redditor or Submission, or a string. When
            a string is provided it will be treated as the name of a Redditor.
        :param text: The flair text to associate with the Redditor or
            Submission (Default: '').
        :param css_class: The css class to associate with the flair html
            (Default: '').

        This method can only be used by an authenticated user who is a
        moderator of the associated Subreddit.

        """
        data = {'css_class': css_class, 'text': text}
        if thing.__class__.__name__ == 'Submission':
            data['link'] = thing.fullname
        else:
            data['name'] = str(thing)
        url = API_PATH['flair'].format(subreddit=self.subreddit)
        self.subreddit._reddit.post(url, data=data)

    def update(self, flair_list, text='', css_class=''):
        """Set or clear the flair for many Redditors at once.

        :param redditor_flair_list: Each item in this list should be either: a
            Redditor name string, a Redditor, or a dictionary containing the
            keys ``user``, ``flair_text``, and ``flair_css_class``. The
            ``user`` key should map to a Redditor name string, or a
            Redditor. When a dictionary isn't provided, or the dictionary is
            missing one of ``flair_text``, or ``flair_css_class`` attributes
            the default values will come from the the following arguments.
        :param text: The flair text to use when not explicitly provided in
            ``flair_list`` (Default: '').
        :param css_class: The css class to use when not explicitly provided in
            ``flair_list`` (Default: '').
        :returns: List of dictionaries indicating the success or failure of
            each update.

        """
        lines = []
        for item in flair_list:
            if isinstance(item, dict):
                fmt_data = (str(item['user']), item.get('flair_text', text),
                            item.get('flair_css_class', css_class))
            else:
                fmt_data = (str(item), text, css_class)
            lines.append('"{}","{}","{}"'.format(*fmt_data))

        response = []
        url = API_PATH['flaircsv'].format(subreddit=self.subreddit)
        while len(lines):
            data = {'flair_csv': '\n'.join(lines[:100])}
            response.extend(self.subreddit._reddit.post(url, data=data))
            lines = lines[100:]
        return response


class SubredditModeration(object):
    """Provides a set of moderation functions to a Subreddit."""

    def __init__(self, subreddit):
        """Create a SubredditModeration instance.

        :param subreddit: The subreddit to moderate.

        """
        self.subreddit = subreddit

    def approve(self, thing):
        """Approve a Comment or Submission.

        :param thing: An instance of Comment or Submission.

        Approving a comment or submission reverts a removal, resets the report
        counter, adds a green check mark indicator (only visible to other
        moderators) on the website view, and sets the ``approved_by`` attribute
        to the authenticated user.

        """
        self.subreddit._reddit.post(API_PATH['approve'],
                                    data={'id': thing.fullname})

    def distinguish(self, thing, how='yes'):
        """Distinguish a Comment or Submission.

        :param thing: An instance of Comment or Submission.

        :param how: One of 'yes', 'no', 'admin', 'special'. 'yes' adds a
            moderator level distinguish. 'no' removes any distinction. 'admin'
            and 'special' require special user priviliges to use.

        """
        return self.subreddit._reddit.post(
            API_PATH['distinguish'], data={'how': how, 'id': thing.fullname})

    def ignore_reports(self, thing):
        """Ignore future reports on a Comment or Submission.

        :param thing: An instance of Comment or Submission.

        Calling this method will prevent future reports on this Comment or
        Submission from both triggering notifications and appearing in the
        various moderation listings. The report count will still increment on
        the Comment or Submission.

        """
        self.subreddit._reddit.post(API_PATH['ignore_reports'],
                                    data={'id': thing.fullname})

    def inbox(self, **generator_kwargs):
        """Return a ListingGenerator for moderator messages.

        Additional keyword arguments are passed to the ``ListingGenerator``
        constructor.

        See ``unread`` for unread moderator messages.

        """
        return ListingGenerator(
            self.subreddit._reddit, API_PATH['moderator_messages'].format(
                subreddit=self.subreddit), **generator_kwargs)

    def remove(self, thing, spam=False):
        """Remove a Comment or Submission.

        :param thing: An instance of Comment or Submission.
        :param spam: When True, use the removal to help train the Subreddit's
            spam filter (Default: False)

        """
        data = {'id': thing.fullname, 'spam': bool(spam)}
        self.subreddit._reddit.post(API_PATH['remove'], data=data)

    def settings(self):
        """Get the subreddit's current settings."""
        url = API_PATH['subreddit_settings'].format(subreddit=self.subreddit)
        return self.subreddit._reddit.get(url)['data']

    def undistinguish(self, thing):
        """Remove mod, admin or special distinguishing on object.

        :returns: The json response from the server.

        """
        return self.distinguish(thing, how='no')

    def unignore_reports(self, thing):
        """Resume receiving future reports on a Comment or Submission.

        :param thing: An instance of Comment or Submission.

        Future reports on this Comment or Submission will cause notifications,
        and appear in the various moderation listings.

        """
        self.subreddit._reddit.post(API_PATH['unignore_reports'],
                                    data={'id': thing.fullname})

    def unread(self, **generator_kwargs):
        """Return a ListingGenerator for unread moderator messages.

        Additional keyword arguments are passed to the ``ListingGenerator``
        constructor.

        See ``inbox`` for all messages.

        """
        return ListingGenerator(
            self.subreddit._reddit, API_PATH['moderator_unread'].format(
                subreddit=self.subreddit), **generator_kwargs)

    def update_settings(self, **kwargs):
        """Update the subreddit's settings.

        See :meth:`Subreddit._create_or_update` for details on each parameter.
        Unspecified attributes will stay the same.

        """
        current_settings = self.settings()
        fullname = current_settings.pop('subreddit_id')

        # These attributes come out using different names than they go in.
        remap = {'lang': 'language',
                 'allow_top': 'default_set',
                 'exclude_modqueue_banned': 'exclude_banned_modqueue',
                 'link_type': 'content_options',
                 'show_media': 'show_media_preview'}
        for (new, old) in remap.items():
            current_settings[new] = current_settings.pop(old)

        current_settings.update(kwargs)
        return Subreddit._create_or_update(_reddit=self.subreddit._reddit,
                                           sr=fullname, **current_settings)


class SubredditRelationship(object):
    """Represents a relationship between a redditor and subreddit."""

    def __init__(self, subreddit, relationship):
        """Create a SubredditRelationship instance.

        :param subreddit: The subreddit for the relationship.
        :param relationship: The name of the relationship.

        """
        self.relationship = relationship
        self.subreddit = subreddit

    def __iter__(self):
        """Iterate through the Redditors belonging to this relationship."""
        url = API_PATH[self.relationship].format(subreddit=self.subreddit)
        params = {'unique': self.subreddit._reddit._next_unique}
        for item in self.subreddit._reddit.get(url, params=params):
            yield item

    def add(self, redditor):
        """Add ``redditor`` to this relationship.

        :param redditor: A string or :class:`~.Redditor` instance.

        """
        data = {'name': str(redditor), 'r': str(self.subreddit),
                'type': self.relationship}
        return self.subreddit._reddit.post(API_PATH['friend'], data=data)

    def remove(self, redditor):
        """Remove ``redditor`` from this relationship.

        :param redditor: A string or :class:`~.Redditor` instance.

        """
        data = {'name': str(redditor), 'r': str(self.subreddit),
                'type': self.relationship}
        return self.subreddit._reddit.post(API_PATH['unfriend'], data=data)


class SubredditStream(object):
    """Provides submission and comment streams."""

    def __init__(self, subreddit):
        """Create a SubredditStream instance.

        :param subreddit: The subreddit associated with the streams.

        """
        self.subreddit = subreddit

    def comments(self):
        """Yield new comments as they become available.

        Comments are yielded oldest first. Up to 100 historial comments will
        initially be returned.

        """
        return stream_generator(self.subreddit.comments)

    def submissions(self):
        """Yield new submissions as they become available.

        Submissions are yielded oldest first. Up to 100 historial submissions
        will initially be returned.

        """
        return stream_generator(self.subreddit.new)


class SubredditWiki(object):
    """Provides a set of moderation functions to a Subreddit."""

    def __getitem__(self, page_name):
        """Lazily return the WikiPage for the subreddit named ``page_name``."""
        return WikiPage(self.subreddit._reddit, self.subreddit, page_name)

    def __init__(self, subreddit):
        """Create a SubredditModeration instance.

        :param subreddit: The subreddit to moderate.

        """
        self.banned = SubredditRelationship(subreddit, 'wikibanned')
        self.contributors = SubredditRelationship(subreddit, 'wikicontributor')
        self.subreddit = subreddit

    def __iter__(self):
        """Iterate through the pages of the wiki."""
        response = self.subreddit._reddit.get(
            API_PATH['wiki_pages'].format(subreddit=self.subreddit),
            params={'unique': self.subreddit._reddit._next_unique})
        for page_name in response['data']:
            yield WikiPage(self.subreddit._reddit, self.subreddit, page_name)

    def create(self, name, content, reason=None, **other_settings):
        """Create a new wiki page.

        :param name: The name of the new WikiPage. This name will be normalied.
        :param content: The content of the new WikiPage.
        :param reason: (Optional) The reason for the creation.
        :param **other_settings: Additional keyword arguments to pass.

        """
        name = name.replace(' ', '_').lower()
        new = WikiPage(self.subreddit._reddit, self.subreddit, name)
        new.edit(content=content, reason=reason, **other_settings)
        return new
