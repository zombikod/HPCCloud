#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright 2016 Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import jsonschema

from girder.models.model_base import ValidationException, AccessControlledModel
from girder.constants import AccessType
from . import schema

from ..utility import get_hpccloud_folder, share_folder, to_object_id, \
    get_simulations_folder

from ..constants import SIMULATIONS_FOLDER


class Project(AccessControlledModel):

    def __init__(self):
        super(Project, self).__init__()

    def initialize(self):
        self.name = 'projects'

    def validate(self, project):
        """
        Validate using jsonschema
        """
        try:
            ref_resolver = jsonschema.RefResolver.from_schema(
                schema.definitions)
            jsonschema.validate(project, schema.project, resolver=ref_resolver)
        except jsonschema.ValidationError as ve:
            raise ValidationException(ve.message)

        return project

    def create(self, user, project):
        """
        Create a new project

        Create a new folder to associate with this project:

        <user>/Private/HPCCloud/<project>

        """
        project['userId'] = user['_id']

        self.validate(project)

        # We need to create the project folder
        hpccloud_folder = get_hpccloud_folder(user)
        project_folder = self.model('folder').createFolder(
            hpccloud_folder, project['name'], parentType='folder',
            creator=user)

        # Create the sub directory the whole simulations for this project
        self.model('folder').createFolder(
            project_folder, SIMULATIONS_FOLDER, parentType='folder',
            creator=user)

        self.model('folder').setUserAccess(
            project_folder, user=user, level=AccessType.ADMIN, save=True)
        project['folderId'] = project_folder['_id']
        project = self.setUserAccess(project, user=user, level=AccessType.ADMIN)
        project = self.save(project)

        return project

    def update(self, user, project, name=None, metadata=None):
        """
        Update an existing project, this involves update the data property.
        For now we will just do a dict update, in the future we might want
        more complex merging.
        :param user: The user performing the update
        :param project: The project object being updated
        :param project: The project name
        :param metadata: The new data object
        :returns: The updated project
        """
        if metadata:
            project.setdefault('metadata', {}).update(metadata)

        if name:
            project['name'] = name
        self.save(project)

    def delete(self, user, project):
        """
        Delete a give project.

        This will clean up any folders, item or files associated with it as well
        a removing the document.

        :param user: The user deleting the project
        :param project: The project to delete.
        """

        # Prevent the deletion of a project that contains simulations
        query = {
            "projectId": project['_id']
        }

        sim = self.model('simulation', 'hpccloud').findOne(query=query)
        if sim is not None:
            raise ValidationException(
                'Unable to delete project that contains simulations')

        # Clean up the project folder
        project_folder = self.model('folder').load(
            project['folderId'], user=user)
        self.model('folder').remove(project_folder)

        super(Project, self).remove(project)

    def share(self, sharer, project, users, groups):
        """
        Share a give project.
        :param sharer: The user sharing the project
        :param project: The project being shared
        :param users: The users to share the project with.
        :param groups: The groups to share the project with.
        """

        access_list = project['access']
        access_list['users'] \
            = [user for user in access_list['users'] if user != sharer['_id']]
        access_list['groups'] = []

        for user_id in users:
            access_object = {
                'id': to_object_id(user_id),
                'level': AccessType.READ
            }
            access_list['users'].append(access_object)

        for group_id in groups:
            access_object = {
                'id': to_object_id(group_id),
                'level': AccessType.READ
            }
            access_list['groups'].append(access_object)

        project_folder = self.model('folder').load(
            project['folderId'], user=sharer)

        # Share the project folder
        share_folder(
            sharer, project_folder, users, groups, level=AccessType.READ,
            recurse=True)

        # We need to share the _simulations folder, with WRITE access, so the
        # user can create simulations
        simulations_folder = get_simulations_folder(sharer, project)

        share_folder(sharer, simulations_folder, users, groups,
                     level=AccessType.ADMIN)

        # Now share any simulation associated with this project
        query = {
            "projectId": project['_id']
        }
        sims = self.model('simulation', 'hpccloud').find(query=query)
        for sim in sims:
            self.model('simulation', 'hpccloud').share(
                sharer, sim, users, groups)

        return self.save(project)

    def simulations(self, user, project):
        """
        Get all the simulation associated with a given project.

        :param user: The user making the request
        :param project: The project to fetch the simulations for.
        """

        query = {
            "projectId": project['_id']
        }

        sims = self.model('simulation', 'hpccloud').find(query=query)

        return list(self.filterResultsByPermission(
                    cursor=sims, user=user, level=AccessType.READ))
