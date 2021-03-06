# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: Julien Anguenot <ja@nuxeo.com>
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
# $Id: catalog.py 31177 2006-03-10 15:39:31Z janguenot $
"""Indexable Object Wrapper for CPS.
"""

from zLOG import LOG, WARNING

from Acquisition import aq_parent
from Acquisition import aq_inner
from Acquisition import aq_base

from DateTime.DateTime import DateTime

from Products.CMFCore.utils import getToolByName

from Products.CPSCore.ProxyBase import ProxyBase
from Products.CPSCore import utils as cpsutils
from Products.CPSDocument.CPSDocument import CPSDocument

DUBLIN_CORE_DATES = ('created', 'effective', 'expires', 'modified')

class IndexableObjectWrapper:
    """This is a CPS adaptation of
    CMFCore.CatalogTool.IndexableObjectWrapper"""

    def __init__(self, vars, ob, lang=None, uid=None):
        self.__vars = vars
        self.__ob = ob
        self.__lang = lang
        self.__uid = uid

        # lazy attributes (getattr makes infinite loops)
        self.__ob_repo = None
        self.__datamodel = None

    def getRepoDoc(self):
        doc = self.__ob_repo
        if doc is not None:
            return doc

        self.__ob_repo = self.__ob.getContent(lang=self.__lang)
        return self.__ob_repo
        
    def getDataModel(self):
        dm = self.__datamodel
        if dm is not None:
            return dm

        self.__datamodel = self.getRepoDoc().getDataModel(proxy=self.__ob)
        return self.__datamodel

    def __getattr__(self, name):
        """This is the indexable wrapper getter for CPS,
        proxy try to get the repository document attributes,
        document in the repository hide some attributes to save some space."""
        vars = self.__vars
        if vars.has_key(name):
            ret = vars[name]
            # Here, deal with DateTime object values.
            if isinstance(ret, DateTime):
                ret = ret.ISO()
            return ret
        ob = self.__ob
        proxy = None
        if isinstance(ob, ProxyBase):
            proxy = ob
            if name not in ('getId', 'id', 'getPhysicalPath', 'uid',
                            'modified',
                            'getDocid', 'isCPSFolderish'):
                # These attributes are computed from the proxy
                ob = self.getRepoDoc()

        if isinstance(ob, CPSDocument):
            # get the computed field value
            ret = self.getDataModel().get(name)
        if not isinstance(ob, CPSDocument) or ret is None:
            try:
                ret = getattr(ob, name)
            except AttributeError:
                if name == 'meta_type':
                    # this is a fix for TextIndexNG2
                    return None
                raise
    
        if proxy is not None and name == 'SearchableText':
            # we add proxy id to searchableText
            ret = ret() + ' ' + proxy.getId()

        # use callable result if needed
        # XXX GR: problem when it is portal_url for instance (think ack).
        # It's useless except in the case of DateTime instances, because
        # it is done by the next layer, nuxeo.lucene, which doesn't know about DateTime.
        if callable(ret) and name in DUBLIN_CORE_DATES:
            ret = ret()

        # Check here if it's a date and return a string representation
        # of the date since DateTime is not a Python standard object
        if isinstance(ret, DateTime):
            ret = ret.ISO()

        return ret

    def allowedRolesAndUsers(self):
        """
        Return a list of roles, users and groups with View permission.
        Used by PortalCatalog to filter out items you're not allowed to see.
        """
        return cpsutils.getAllowedRolesAndUsersOfObject(self.__ob)

    def localUsersWithRoles(self):
        """
        Return a list of users and groups having local roles.
        Used by PortalCatalog to find which objects have roles for given
        users and groups.
        Only return proxies: see above __getattr__ raises
        AttributeError when accessing this attribute.
        """
        ob = self.__ob
        local_roles = ['user:%s' % r[0] for r in ob.get_local_roles()]
        local_roles.extend(
            ['group:%s' % r[0] for r in ob.get_local_group_roles()])
        return local_roles

    def path(self):
        """PathIndex needs a path attribute, otherwise it uses
        getPhysicalPath which fails for viewLanguage paths."""
        if self.__uid is not None:
            return self.__uid
        else:
            return self.__ob.getPhysicalPath()

    def container_path(self):
        """This is used to produce an index
        return the parent full path."""
        return '/'.join(self.__ob.getPhysicalPath()[:-1])

    def relative_path(self):
        """This is used to produce a metadata
        return a path relative to the portal."""
        utool = getToolByName(self, 'portal_url', None)
        ret = ''
        if utool:
            # broken object can't aquire portal_url
            ret = utool.getRelativeContentURL(self.__ob)
        return ret

    def relative_path_depth(self):
        """This is used to produce an index
        return the path depth relative to the portal."""
        rpath = self.relative_path()
        ret = -1
        if rpath:
            ret = rpath.count('/')+1
        return ret

    def position_in_container(self):
        """Return the object position in the container."""
        ob = self.__ob
        container = aq_parent(aq_inner(ob))
        if getattr(aq_base(container), 'getObjectPosition', None) is not None:
            try:
                return container.getObjectPosition(ob.getId())
            except ValueError, err:
                # Trying to index a doc before it is created ?
                LOG('position_in_container', WARNING,
                    'got a Value Error %s' % err)
                return 0
            except AttributeError, err:
                # Container without ordering support such as
                # BTreeFolder based folders. (proxy or not)
                LOG('position_in_container', WARNING,
                    'got an AttributeError %s' % err)
                return 0
        return 0

    def match_languages(self):
        """Return a list of languages that the proxy matches."""
        ob = self.__ob
        proxy_language = self.__lang
        if proxy_language is None:
            utool = getToolByName(self, 'portal_url', None)
            if utool:
                # match_languages is used only with UI locales
                portal = utool.getPortalObject()
                return portal.getProperty('available_languages',
                                          cpsutils.ALL_LOCALES)
            return cpsutils.ALL_LOCALES
        languages = [proxy_language]
        if ob.getDefaultLanguage() == proxy_language:
            languages.extend([lang for lang in cpsutils.ALL_LOCALES
                              if lang not in ob.getProxyLanguages()])
        return languages

