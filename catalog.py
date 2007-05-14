# (C) Copyright 2006-2007 Nuxeo SAS <http://nuxeo.com>
# Authors:
# Julien Anguenot <ja@nuxeo.com>
# Lennart Regebro
# M.-A. Darche <madarche@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# $Id$
"""CPS Lucene Catalog
"""

import time
import logging
import gc
from sets import Set
from urlparse import urlsplit

import transaction

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.CMFCore.utils import SimpleItemWithProperties
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import _getAuthenticatedUser
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.CatalogTool import CatalogTool

import zope.interface
from zope.component.interfaces import ComponentLookupError
from zope.app import zapi

from nuxeo.lucene.interfaces import ILuceneCatalog
from nuxeo.lucene.catalog import LuceneCatalog

from Products.CPSCore.ProxyBase import ProxyBase
from Products.CPSCore import utils as cpsutils

from Products.CPSUtil.timer import Timer

from zcatalogquery import ZCatalogQuery
from brain import CPSBrain
from wrapper import IndexableObjectWrapper

from interfaces import ICPSLuceneCatalogTool

import filelock

logger = logging.getLogger("CPSLuceneCatalog")

LOCK_FILE_BASE_NAME = 'cpslucenecatalog'


class CPSLuceneCatalogTool(CatalogTool):
    """CPS Lucene Catalog
    """

    zope.interface.implements(ICPSLuceneCatalogTool)

    id = "portal_catalog"
    meta_type = "CPS Lucene Catalog Tool"

    security = ClassSecurityInfo()

    # default properties
    server_url = 'http://localhost:9180'
    multilanguage_support = True


    def __init__(self):
        utility = LuceneCatalog(self.server_url)
        self._setOb('_catalog', utility)

        # BBB for CPS <= 3.4
        self.Indexes = self

    def  __setattr__(self, id, value):
        if id == 'server_url':
            if not value.startswith('http://'):
                value = 'http://' + value
            logger.info("Update nuxeo.lucene.catalog properties")
            setattr(self.getCatalog(), id, value)
            self._refreshCatalogProxy()
        CatalogTool.__setattr__(self, id, value)

    def __url(self, ob):
        # XXX It would be better to have uid instead of rpath here.
        return '/'.join( ob.getPhysicalPath() )

    def _refreshCatalogProxy(self):
        """Refresh the cached proxy
        """
        # Activate persistency
        self.getCatalog()._p_changed = 1
        # Remove cached proxy
        self.getCatalog()._v_proxy = None

    def getCatalog(self):
       return self._catalog

    def __len__(self):
        return len(self.getCatalog())

    def __nonzero__(self):
        return True

    def getServerHostAndPort(self):
        """Return a tuple with server host and server port.
        """
        network_location_str = urlsplit(self.server_url)
        network_location = network_location_str[1].split(':')
        server_host = network_location[0]
        server_port = (len(network_location) > 1 and network_location[1]
                       or '80')
        res = (server_host, server_port)
        return res

    def getLockfileName(self):
        (server_host, server_port) = self.getServerHostAndPort()
        lock_file_name = '-'.join((LOCK_FILE_BASE_NAME,
                                   server_host, server_port))
        return lock_file_name

    #
    # API : Column
    #

    security.declareProtected(ManagePortal, 'addColumn')
    def addColumn(self, name, default_value=None):
        return self.getCatalog().addColumn(name, default_value)

    #
    # API : Fields

    security.declareProtected(ManagePortal, 'addField')
    def addField(self, **kw):
        self.getCatalog().addFieldFor(iface=None, **kw)

    security.declareProtected(ManagePortal, 'getFieldTypes')
    def getFieldTypes(self):
        # XXX : hardcoded for now and not complete
        fields =  (
            'Keyword',
            'MultiKeyword', # XXX will disappear in the future.
            'Text',
            'UnStored',
            'UnIndexed',
            'Date',
            'Path',
            'Sort',
            )
        return fields

    security.declareProtected(ManagePortal, 'getFieldConfs')
    def getFieldConfs(self):
        # It applies globally for now. nuxeo.lucene can discriminate
        # by iface though.
        cpsres = ()
        fieldconfs = self.getCatalog().getFieldConfigurationsFor()
        for each in fieldconfs:
            cpsres += (
                {'name' : each.name,
                 'attribute' : each.attribute,
                 'type' : each.type,
                 'analyzer' : each.analyzer,
                 },)
        return cpsres

    def clean(self):
        return self.getCatalog().clean()

    def _search(self, REQUEST=None, **kw):

        #t = Timer('CPSLuceneCatalog._search', level=logging.DEBUG)

        return_fields = kw.pop('columns', ())
        # Construct query for nuxeo.lucene.catalog
        query = ZCatalogQuery(self, REQUEST, **kw)

        #t.mark('Convert Query')

        results, nb_results = self.getCatalog().searchResults(
            search_fields=query.getFieldsMap(),
            options=query.getQueryOptions(),
            return_fields=return_fields,
            )

        #t.mark('NXLucene query request')

        # Construct lite brains for BBB
        brains = []
        for mapping in results:
            one = CPSBrain(mapping).__of__(self)
            setattr(one, 'out_of', nb_results)
            brains.append(one)
        #t.mark('Construct %s brain(s)' % str(len(brains)))
        #t.log()
        return brains

    def searchResults(self, REQUEST=None, **kw):
        """Searching with CPS security indexes.
        """
        #logger.debug("SeachResults %s" % str(kw))
        user = _getAuthenticatedUser(self)
        kw[ 'allowedRolesAndUsers' ] = self._listAllowedRolesAndUsers(user)

        return self._search(REQUEST, **kw)

    # Override CMFCore.CatalogTool alias
    __call__ = searchResults

    def unrestrictedSearchResults(self, REQUEST=None, **kw):
        """Calls ZCatalog.searchResults() without any CMF-specific processing.

        o Permission:  Private (Python only)
        """
        #logger.debug("unrestrictedSearchResults %s" % str(kw))
        return self._search(REQUEST, **kw)

    def reindexObject(self, object, idxs=[], update_metadata=1, uid=None):
        """ Update 'object' in catalog.

        o 'idxs', if passed, is a list of specific indexes to update
          (by default, all indexes are updated).

        o If 'update_metadata' is True, then update the metadata record
          in the catalog as well.

        o Permission:  Private (Python only)
        """
        #logger.debug("reindexObject %s idxs=%s update_metdata=%s" % (
            #str(object), str(idxs), str(update_metadata)))
        if uid is None:
            uid = self.__url(object)

        # Filter out invalid indexes will be done at nuxeo.lucene level.
        self.catalog_object(object, uid, idxs, update_metadata)

    def unindexObject(self, object):
        """ Remove 'object' from the catalog.

        o Permission:  Private (Python only)
        """

        # Don't index repository objects or anything under them.
        repotool = getToolByName(self, 'portal_repository', None)
        if repotool is not None and repotool.isObjectUnderRepository(object):
            return

        #logger.debug("unindexObject %s" % str(object))

        default_uid = self._CatalogTool__url(object)
        proxy = None
        if isinstance(object, ProxyBase):
            proxy = object
            languages = proxy.getProxyLanguages()
        if proxy is None or len(languages) == 1:
            self.uncatalog_object(default_uid)
        else:
            for language in languages:
                # remove all translation of the proxy
                uid = default_uid + '/%s/%s' % (cpsutils.KEYWORD_VIEW_LANGUAGE,
                                                language)
                self.uncatalog_object(uid)

    def catalog_object(self, object, uid, idxs=[], update_metadata=1,
                       pghandler=None):

        # Don't index repository objects or anything under them.
        repotool = getToolByName(self, 'portal_repository', None)
        if repotool is not None and repotool.isObjectUnderRepository(object):
            return

        # BBB: for Zope 2.7, which doesn't take a pghandler
        if pghandler is None:
            pgharg = ()
        else:
            pgharg = (pghandler,)

        #logger.debug("catalog_object %s" % str(object))

        wf = getattr(self, 'portal_workflow', None)
        if wf is not None:
            vars = wf.getCatalogVariablesFor(object)
        else:
            vars = {}

        # Workaround for a Lucene problem:
        # In lucene, you can not get the data out from an unindexed or
        # unstored field. And since reindexing means unindexing and then
        # re-indexing a record, this means that if you don't pass the data
        # for unindexed or unstored fields, these will be cleared.
        # Therefore, when specifying which indexes to reindex, we here make
        # sure that all unindexed and unstored fields are included:
        if idxs:
            idxs = list(idxs)
            for idx in self.getCatalog().getFieldConfigurationsFor():
                if (idx.type.lower() in ('unindexed', 'unstored', 'sort') and
                    idx.name not in idxs):
                    idxs.append(idx.name)

        # Not a proxy.
        if not isinstance(object, ProxyBase):
            w = IndexableObjectWrapper(vars, object)
            self.getCatalog().index(uid, w, idxs)
            return

        # Proxy with a viewLanguage uid.
        # Happens when the catalog is reindexed (refreshCatalog)
        # or when called by reindexObjectSecurity.
        path = uid.split('/')
        if cpsutils.KEYWORD_VIEW_LANGUAGE in path:
            if path.index(cpsutils.KEYWORD_VIEW_LANGUAGE) == len(path)-2:
                lang = path[-1]
            else:
                # Weird, but don't crash
                lang = None
            w = IndexableObjectWrapper(vars, object, lang, uid)
            self.getCatalog().index(uid, w, idxs)
            return

        # We reindex a normal proxy.
        had_languages = []
        uid_view = uid + '/' + cpsutils.KEYWORD_VIEW_LANGUAGE
        if self.multilanguage_support:
            # Find what languages are in the catalog for this proxy
            for brain in self.unrestrictedSearchResults(path=uid_view, columns=('uid',)):
                path = brain.getPath()
                had_languages.append(path[path.rindex('/')+1:])

        # Do we now have only one language?
        languages = object.getProxyLanguages()
        if len(languages) == 1:
            # Remove previous languages
            for lang in had_languages:
                self.uncatalog_object(uid_view+'/'+lang)
            # Index normal proxy
            w = IndexableObjectWrapper(vars, object)
            self.getCatalog().index(uid, w, idxs)
            return

        # We now have several languages (or none).
        # Remove old base proxy path
        if self.getCatalog().hasUID(uid):
            self.uncatalog_object(uid)
        # Also remove old languages
        for lang in had_languages:
            if lang not in languages:
                self.uncatalog_object(uid_view+'/'+lang)
        # Index all available translations of the proxy
        # with uid/viewLanguage/language for path
        for lang in languages:
            uid = uid_view + '/' + lang
            w = IndexableObjectWrapper(vars, object, lang, uid)
            self.getCatalog().index(uid, w, idxs)

    def uncatalog_object(self, uid):
        self.getCatalog().unindex(uid)

    #
    # BBB for CPS <= 3.4
    #

    def objectValues(self, spec=None):
        return []

    # part of ZCatalog api
    def indexes(self):
        idxs = self.getCatalog().getFieldNamesFor()
        return idxs

    def addIndex(self, name, type,extra=None):
        pass

    security.declareProtected(ManagePortal, 'hasUID')
    def hasUID(self, uid):
        "Checks if a certain UID is indexed"
        return self._catalog.hasUID(uid)

    def uniqueValuesFor(self, name):
        """Return the unique values for a given FieldIndex

        For Lucene this will return all the terms for a given field, no
        matter what type. I don't promise it's unique (but it should be) or
        sensible, because I haven't verified that it is is all cases.
        /regebro"""
        return self._catalog.getFieldTerms(name)

    def removeDefunctEntries(self):
        # Goes through the whole catalog and removed entries that no
        # longer exists.
        self._synchronize(index_missing=0,remove_defunct=1)

    def _obtainLock(self):
        lock_file_name = self.getLockfileName()
        if not filelock.PythonFileLock(lock_file_name).obtain():
            raise ValueError("Another process is already reindexing or "
                             "synchronizing this catalog. "
                             "If this is not the case you can remove the "
                             "%s lock file in the temporary directory of "
                             "the server running Zope." % lock_file_name
                             )

    def _releaseLock(self):
        lock_file_name = self.getLockfileName()
        filelock.PythonFileLock(lock_file_name).release()

    def indexProxies(self, idxs=(), from_path=''):
        # Indexes all proxies under from_path
        # If from_path is none, indexes all proxies.
        self._obtainLock()
        pxtool = getToolByName(self, 'portal_proxies')
        rpaths = pxtool._rpath_to_infos.keys(from_path, from_path+'\xFF')
        self._indexPaths(rpaths, idxs=idxs)
        self._releaseLock()

    def _indexPaths(self, rpaths, idxs=()):
        """Indexes a list of paths (rpaths or physical paths both work).
        """
        start = time.time()

        reindexed = 0

        utool = getToolByName(self, 'portal_url')
        portal = utool.getPortalObject()
        portal_path = utool.getPortalPath()

        # When reindexing the WHOLE catalog, as we do here, the language
        # support is pointless, as it's there to reindex all languages of a
        # proxy, even when you reindex only one of them. Here they all get
        # reindexed sooner or later anyway:

        if self.multilanguage_support:
            self.multilanguage_support = False
            enable_multilanguage_support = True
        else:
            enable_multilanguage_support = False

        # Also, the asynchronous reindexing is pretty pointless here too:
        catalog = self.getCatalog()
        catalog._txn_async = False

        for rpath in rpaths:
            proxy = portal.unrestrictedTraverse(rpath)
            self.reindexObject(proxy, idxs=list(idxs))
            transaction.commit()
            reindexed +=1
            proxy._p_deactivate()

            if reindexed % 100 == 0:
                gc.collect()

            logger.debug("Proxy number %s reindexed:\n%s" % (str(reindexed), rpath))

        gc.collect()

        stop = time.time()
        logger.info("Reindexation done in %s seconds" % str(stop-start))

        # Reset the multi_language_support and _txn_async
        if enable_multilanguage_support:
            self.multilanguage_support = True
        catalog._txn_async = True
        # Optimize
        catalog.optimize()


    def _synchronize(self, idxs=(), remove_defunct=1, index_missing=1):
        """Synchronize the index with the documents.

        This method will index proxies that are not indexed and remove
        index-entries that no longer have corresponding proxies.
        """
        self._obtainLock()
        res = []
        start_time = time.time()
        logger.info("Start index synchronization")

        # Get all indexed rpaths:
        all_indexed = self.uniqueValuesFor('uid')
        get_time = time.time()
        logger.info("Getting all UIDs: %s seconds" % (get_time - start_time))

        # Get all rpaths:
        pxtool = getToolByName(self, 'portal_proxies')
        rpaths = pxtool._rpath_to_infos
        rpath_time = time.time()
        logger.info("Getting all rpaths: %s seconds" % (rpath_time - get_time))

        # Diff:
        all_indexed = Set(all_indexed)
        rpathset = Set()
        portal_path = '/'.join(
            self.portal_url.getPortalObject().getPhysicalPath())
        for rpath in rpaths:
            path = portal_path + '/' + rpath
            rpathset.add(path)

        prepare_time = time.time()
        logger.info("Preparing for diff: %s seconds" % (prepare_time -
                                                        rpath_time))

        defunct = all_indexed - rpathset
        defunct_time = time.time()
        logger.info("Getting all defuncts: %s seconds" % (defunct_time -
                                                          prepare_time))

        count = 0
        for each in defunct:
            count += 1
            if remove_defunct:
                self.uncatalog_object(each)
                logger.debug("Object %s doesn't exist and is removed from "
                              "the catalog" % each)
            else:
                logger.debug("Object %s doesn't exist and can be removed "
                              "the catalog" % each)

        if remove_defunct:
            # Optimize the store after the unindexing
            self.getCatalog().optimize()


        logger.info("Total number of defunct entries: %s" % count)
        unindexed_time = time.time()
        if remove_defunct:
            logger.info("Unindexed in %s seconds" % (unindexed_time -
                                                      defunct_time))

        nonindexed = rpathset - all_indexed
        ni_time = time.time()
        logger.info("Getting all non-indexed: %s seconds" % (ni_time -
                                                             unindexed_time))
        logger.info("Total number of non-indexed entries: %s" % len(nonindexed))

        if index_missing:
            self._indexPaths(nonindexed, idxs=idxs)

        # Make another optimization. For some reason, after unindexing, you
        # need to optimize twice for the uids to be removed from the list of
        # terms. So we do that here, for good measure:
        if index_missing or remove_defunct:
            self.getCatalog().optimize()

        logger.info("Total time: %s seconds" %
                    (time.time() - start_time))
        self._releaseLock()


    #
    # ZMI
    #

    _properties = CatalogTool._properties + (
        # The server_url property is here only to display its value in ZMI, its
        # actual value is on the nuxeo.lucene catalog utility
        {'id': 'server_url', 'type': 'string', 'mode': 'w',
         'label': 'xml-rpc server URL',
         },
        {'id': 'multilanguage_support', 'type': 'boolean', 'mode': 'w',
         'label': 'Multi-language support',
         },
        )

    manage_options = (CatalogTool.manage_options[2],
                      { 'label' : 'Manage XML-RPC Server',
                        'action' : 'manage_advancedForm',
                        },
                      { 'label' : 'Schema',
                        'action' : 'manage_catalogSchema',
                        },
                      { 'label' : 'Fields',
                        'action' : 'manage_catalogFields',
                        },
                      )

    security.declareProtected(ManagePortal, 'manage_advancedForm')
    manage_advancedForm = PageTemplateFile(
        'zmi/manage_advancedForm.pt', globals())

    security.declareProtected(ManagePortal, 'manage_catalogFields')
    manage_catalogFields = PageTemplateFile(
        'zmi/manage_catalogFields.pt', globals())

    security.declareProtected(ManagePortal, 'manage_catalogSchema')
    manage_catalogSchema = PageTemplateFile(
        'zmi/manage_catalogSchema.pt', globals())

    security.declareProtected(ManagePortal, 'manage_reindexProxies')
    def manage_reindexProxies(self, idxs=(), from_path='', REQUEST=None):
        """Reindex  an existing complete CPS instance with content.

        It checks all the CPS proxies from the proxies tool.
        """

        self.indexProxies(idxs=idxs, from_path=from_path)

        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(
                self.absolute_url() + '/manage_advancedForm')

    security.declareProtected(ManagePortal, 'manage_reindexSelectedFields')
    def manage_reindexSelectedFields(self, fields=(), REQUEST=None):
        """Reindex selected fields.
        """
        if fields:
            self.manage_reindexProxies(idxs=fields, REQUEST=REQUEST)
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(
                self.absolute_url() + '/manage_catalogFields')

    security.declareProtected(ManagePortal, 'manage_optimize')
    def manage_optimize(self, REQUEST=None):
        """Optimier the indexes store
        """
        self.getCatalog().optimize()
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(
                self.absolute_url() + '/manage_advancedForm')

    security.declareProtected(ManagePortal, 'manage_clean')
    def manage_clean(self, REQUEST=None):
        """CLean the indexes store.
        """
        self.clean()
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(
                self.absolute_url() + '/manage_advancedForm')

    security.declareProtected(ManagePortal, 'manage_synchronize')
    def manage_synchronize(self, index_missing=0,remove_defunct=0, REQUEST=None):
        """Remove objects that no longer exist
        """
        self._synchronize(index_missing=index_missing,
                          remove_defunct=index_missing)
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(
                self.absolute_url() + '/manage_advancedForm')
InitializeClass(CPSLuceneCatalogTool)
