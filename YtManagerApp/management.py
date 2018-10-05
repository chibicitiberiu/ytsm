from .models import SubscriptionFolder, Subscription, Video


class FolderManager(object):

    @staticmethod
    def create_or_edit(fid, name, parent_id):
        # Create or edit
        if fid == '#':
            folder = SubscriptionFolder()
        else:
            folder = SubscriptionFolder.objects.get(id=int(fid))

        # Set attributes
        folder.name = name
        if parent_id == '#':
            folder.parent = None
        else:
            folder.parent = SubscriptionFolder.objects.get(id=int(parent_id))

        FolderManager.__validate(folder)
        folder.save()

    @staticmethod
    def __validate(folder):
        # Make sure folder name is unique in the parent folder
        for dbFolder in SubscriptionFolder.objects.filter(parent_id=folder.parent_id):
            if dbFolder.id != folder.id and dbFolder.name == folder.name:
                raise ValueError('Folder name is not unique!')

        # Prevent parenting loops
        current = folder
        visited = []

        while not (current is None):
            if current in visited:
                raise ValueError('Parenting cycle detected!')
            visited.append(current)
            current = current.parent

    @staticmethod
    def delete(fid: int):
        folder = SubscriptionFolder.objects.get(id=fid)
        folder.delete()
