#! /usr/bin/env python
import unittest

from __init__ import get_connection
from auth import authenticate, P2PAuthError
import cache
import inspect
import sys

import pprint
pp = pprint.PrettyPrinter(indent=4)


class TestP2P(unittest.TestCase):
    def setUp(self):
        self.content_item_slug = 'chi-na-lorem-a'
        self.collection_slug = 'chi_na_lorem'
        self.p2p = get_connection()
        self.p2p.debug = True
        self.p2p.config['IMAGE_SERVICES_URL'] = 'http://image.p2p.tribuneinteractive.com'
        self.maxDiff = None

        self.content_item_keys = ('altheadline', 'expire_time',
                'canonical_url', 'mobile_title', 'create_time',
                'source_name', 'last_modified_time', 'seodescription',
                'exclusivity', 'content_type_group_code', 'byline',
                'title', 'dateline', 'brief', 'id', 'web_url', 'body',
                'display_time', 'publish_time', 'undated', 'is_opinion',
                'columnist_id', 'live_time', 'titleline',
                'ad_exclusion_category', 'product_affiliate_code',
                'content_item_state_code', 'seo_redirect_url', 'slug',
                'content_item_type_code', 'deckheadline', 'seo_keyphrase',
                'mobile_highlights', 'subheadline', 'thumbnail_url',
                'source_code', 'ad_keywords', 'seotitle', 'alt_thumbnail_url')
        self.collection_keys = ('created_at', 'code', 'name',
                'sequence', 'max_elements', 'productaffiliatesection_id',
                'last_modified_time', 'collection_type_code',
                'exclusivity', 'id')
        self.content_layout_keys = ('code', 'items',
                'last_modified_time', 'collection_id', 'id')
        self.content_layout_item_keys = (
                'content_item_type_code', 'content_item_state_code',
                'sequence', 'headline', 'abstract',
                'productaffiliatesection_id', 'slug', 'subheadline',
                'last_modified_time', 'contentitem_id', 'id')

    def test_get_content_item(self):
        data = self.p2p.get_content_item(self.content_item_slug)
        for k in self.content_item_keys:
            self.assertIn(k, data.keys())

    def test_create_update_delete_content_item(self):
        data = {
            'slug': 'chi_na_test_create_update_delete',
            'title': 'Testing creating, updating and deletion',
            'body': 'lorem ipsum',
            'content_item_type_code': 'story',
        }
        try:
            result = self.p2p.create_content_item(data)
            data2 = data.copy()
            data2['body'] = 'Lorem ipsum foo bar'
            result2 = self.p2p.update_content_item(data2)
        finally:
            self.assertTrue(self.p2p.delete_content_item(data['slug']))

        self.assertIn(data['content_item_type_code'], result)
        res = result[data['content_item_type_code']]
        self.assertEqual(res['slug'], data['slug'])
        self.assertEqual(res['title'], data['title'])
        self.assertEqual(res['body'].strip(), data['body'])

        res = result2
        self.assertEqual(res, {})

    def test_get_collection(self):
        data = self.p2p.get_collection(self.collection_slug)
        for k in self.collection_keys:
            self.assertIn(k, data.keys())

    def test_get_collection_layout(self):
        data = self.p2p.get_collection_layout(self.collection_slug)
        for k in self.content_layout_keys:
            self.assertIn(k, data.keys())

        for k in self.content_layout_item_keys:
            self.assertIn(k, data['items'][0].keys())

    def test_multi_items(self):
        content_item_ids = [58253183, 56809651, 56810874, 56811192, 58253247]
        data = self.p2p.get_multi_content_items(ids=content_item_ids)
        for k in self.content_item_keys:
            self.assertIn(k, data[0].keys())

    def test_many_multi_items(self):
        cslug = 'chicago_breaking_news_headlines'
        clayout = self.p2p.get_collection_layout(cslug)
        ci_ids = [i['contentitem_id'] for i in clayout['items']]

        self.assertTrue(len(ci_ids) > 25)

        data = self.p2p.get_multi_content_items(ci_ids)
        self.assertTrue(len(ci_ids) == len(data))
        for k in self.content_item_keys:
            self.assertIn(k, data[0].keys())

    def test_fancy_collection(self):
        data = self.p2p.get_fancy_collection(
            self.collection_slug, with_collection=True)

        for k in self.content_layout_keys:
            self.assertIn(k, data.keys())

        for k in self.collection_keys:
            self.assertIn(k, data['collection'].keys())

        for k in self.content_layout_item_keys:
            self.assertIn(k, data['items'][0].keys())

        for k in self.content_item_keys:
            self.assertIn(k, data['items'][0]['content_item'].keys())

    def test_fancy_content_item(self):
        data = self.p2p.get_fancy_content_item(
            self.content_item_slug)

        for k in ('title', 'id', 'slug'):
            self.assertIn(k, data['related_items'][0]['content_item'])

        #pp.pprint(data)

    def test_image_services(self):
        data = self.p2p.get_thumb_for_slug(self.content_item_slug)

        self.assertEqual(
            data, {
                u'crops': [],
                u'height': 105,
                u'id': u'turbine/chi-na-lorem-a',
                u'namespace': u'turbine',
                u'size': 6138,
                u'slug': u'chi-na-lorem-a',
                u'url': u'/img-5124e228/turbine/chi-na-lorem-a',
                u'width': 187
            })

    @unittest.skip("Uhhh... not committing my password")
    def test_auth(self):
        self.username = ''
        self.password = ''

        self.badpassword = 'password'

        self.token = 'whatisthis?'

        with self.assertRaises(P2PAuthError) as err:
            userinfo = authenticate(
                username=self.username,
                password=self.badpassword)

        self.assertEqual(err.exception.message,
                         'Incorrect username or password')

        userinfo = authenticate(
            username=self.username, password=self.password)

        #pp.pprint(userinfo)

        self.assertEqual(type(userinfo), dict)

    def test_get_section(self):
        data = self.p2p.get_section('/news/local/breaking')

        self.assertEqual(type(data), dict)
        #pp.pprint(data)


class TestWorkflows(unittest.TestCase):
    def setUp(self):
        self.content_item_slug = 'chi-na-lorem-a'
        self.collection_slug = 'chi_na_lorem'
        self.p2p = get_connection()
        self.p2p.debug = True
        self.maxDiff = None

    def test_publish_story(self):
        """
        Here we are going to create a story, create a photo, attach the photo
        to the story, create a collection, add the story to the collection, and
        supress the story in the collection.
        """
        article_data = {
            'slug': 'chi_na_test_create_update_delete',
            'title': 'Testing creating, updating and deletion',
            'byline': 'By Bobby Tables',
            'body': 'lorem ipsum',
            'content_item_type_code': 'story',
            #'photo_upload': {
                #'alt_thumbnail': {
                    #'url': 'http://media.apps.chicagotribune.com/api_test.jpg'
                #}
            #}
        }
        photo_data = {
            'slug': 'chi_na_test_create_update_delete_photo',
            'title': 'Photo: Testing creating, updating and deletion',
            'caption': 'lorem ipsum',
            'content_item_type_code': 'photo',
            'photo_upload': {
                'alt_thumbnail': {
                    'url': 'http://media.apps.chicagotribune.com/api_test.jpg'
                }
            }
        }

        #self.p2p.delete_content_item(photo_data['slug'])
        #self.p2p.delete_content_item(article_data['slug'])
        #return True

        article = photo = None
        try:
            # Create article
            article = self.p2p.create_content_item(article_data)
            self.assertIn('story', article)
            self.assertEqual(
                article['story']['slug'], article_data['slug'])

            # Create photo
            photo = self.p2p.create_content_item(photo_data)
            self.assertIn('photo', photo)
            self.assertEqual(
                photo['photo']['slug'], photo_data['slug'])

            # Add photo as related item to the article
            self.assertEqual(
                self.p2p.push_into_content_item(
                    article_data['slug'], [photo_data['slug']]),
                {})

            # Add article to a collection
            self.assertEqual(
                self.p2p.push_into_collection(
                    self.collection_slug, [article_data['slug']]),
                {})

            # Suppress the article in the collection
            self.assertEqual(
                self.p2p.suppress_in_collection(
                    self.collection_slug, [article_data['slug']]),
                {})
        finally:
            # Delete the photo
            if photo:
                self.assertTrue(self.p2p.delete_content_item(
                    photo_data['slug']))
            # Delete the article
            if article:
                self.assertTrue(self.p2p.delete_content_item(
                    article_data['slug']))


class TestP2PCache(unittest.TestCase):
    def setUp(self):
        self.content_item_slug = 'chi-na-lorem-a'
        self.collection_slug = 'chi_na_lorem'
        self.p2p = get_connection()
        self.p2p.debug = True
        self.maxDiff = None

    def test_cache(self):
        # Get a list of availabe classes to test
        test_backends = ('DictionaryCache', 'DjangoCache')
        cache_backends = list()
        for backend in test_backends:
            if hasattr(cache, backend):
                cache_backends.append(getattr(cache, backend))

        content_item_ids = [
            58253183, 56809651, 56810874, 56811192, 58253247]

        for cls in cache_backends:
            self.p2p.cache = cls()
            data = self.p2p.get_multi_content_items(ids=content_item_ids)
            data = self.p2p.get_content_item(self.content_item_slug)
            stats = self.p2p.cache.get_stats()
            self.assertEqual(stats['content_item_gets'], 6)
            self.assertEqual(stats['content_item_hits'], 1)

    #@unittest.skip("Beware, will delete everything from redis")
    def test_redis_cache(self):
        content_item_ids = [
            58253183, 56809651, 56810874, 56811192, 58253247]

        self.p2p.cache = cache.RedisCache()
        self.p2p.cache.clear()
        data = self.p2p.get_multi_content_items(ids=content_item_ids)
        data = self.p2p.get_content_item(self.content_item_slug)
        stats = self.p2p.cache.get_stats()
        self.assertEqual(stats['content_item_gets'], 6)
        self.assertEqual(stats['content_item_hits'], 1)

        removed = self.p2p.cache.remove_content_item(self.content_item_slug)
        data = self.p2p.get_content_item(self.content_item_slug)
        stats = self.p2p.cache.get_stats()
        self.assertTrue(removed)
        self.assertEqual(stats['content_item_gets'], 7)
        self.assertEqual(stats['content_item_hits'], 1)


if __name__ == '__main__':
    import logging
    logging.basicConfig()
    log = logging.getLogger()

    # Show debug messages from p2p
    #log.setLevel(logging.DEBUG)

    unittest.main()
