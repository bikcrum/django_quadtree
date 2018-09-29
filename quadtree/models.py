from django.db import models
import json
from time import time


# Create your models here.

class Rectangle(models.Model):
    x = models.FloatField()
    y = models.FloatField()
    w = models.FloatField()
    h = models.FloatField()

    class Meta:
        db_table = "rectangle"

    def contains(self, location):
        return location.longitude >= self.x and location.longitude < self.x + self.w and location.latitude >= self.y and location.latitude < self.y + self.h

    def intersects(self, rect):
        return abs(self.x - rect.x) < (self.w + rect.w) or abs(self.y - rect.y) < (self.y + rect.y)


class QuadTree(models.Model):
    boundary = models.ForeignKey('Rectangle', on_delete=models.CASCADE)
    capacity = models.IntegerField(default=4)
    location_ids = models.CharField(max_length=1000, default='[]')
    divided = models.BooleanField(default=False)
    child_nw = models.ForeignKey('self', on_delete=models.CASCADE, null=True, related_name='child_north_west')
    child_ne = models.ForeignKey('self', on_delete=models.CASCADE, null=True, related_name='child_north_east')
    child_sw = models.ForeignKey('self', on_delete=models.CASCADE, null=True, related_name='child_south_west')
    child_se = models.ForeignKey('self', on_delete=models.CASCADE, null=True, related_name='child_south_east')

    class Meta:
        db_table = "quadtree"

    ### UTILITY FUNCTIONS ###

    def subdivide(self):
        # get bounds
        x = self.boundary.x
        y = self.boundary.y
        w = self.boundary.w
        h = self.boundary.h

        # create sub division bound (4 quaters)
        nw = Rectangle(x=x, y=y + h / 2, w=w / 2, h=h / 2)
        ne = Rectangle(x=x + w / 2, y=y + h / 2, w=w / 2, h=h / 2)
        sw = Rectangle(x=x, y=y, w=w / 2, h=h / 2)
        se = Rectangle(x=x + w / 2, y=y, w=w / 2, h=h / 2)

        # save those quaters
        nw.save()
        ne.save()
        sw.save()
        se.save()

        # create self out of 4 quaters
        child_nw = QuadTree(boundary=nw)
        child_ne = QuadTree(boundary=ne)
        child_sw = QuadTree(boundary=sw)
        child_se = QuadTree(boundary=se)

        child_nw.save()
        child_ne.save()
        child_sw.save()
        child_se.save()

        self.child_nw = child_nw
        self.child_ne = child_ne
        self.child_sw = child_sw
        self.child_se = child_se

        # since its divided
        self.divided = True

        # save current self after subdividing
        self.save()

    def insert(self, location):
        # if location doesn't fit boundary just not right place to insert
        if not self.boundary.contains(location):
            return False

        # get all users id present in current self
        location_ids = json.loads(self.location_ids)

        # ensure no duplicate location get added
        if location.id in location_ids:
            print('location already exist in quadtree', self.id)
            return False

        # if users id count is less than capacity just fill it and return True
        if len(location_ids) < self.capacity:
            location_ids.append(location.id)
            self.location_ids = json.dumps(location_ids)
            # save after updating columns
            self.save()
            print('location added in quadtree', self.id)
            return True

        # we reached here because capacity was full so we need to subdivide if is not divided
        if not self.divided:
            self.subdivide()

        # check right self to insert
        return self.child_nw.insert(location) or \
               self.child_ne.insert(location) or \
               self.child_sw.insert(location) or \
               self.child_se.insert(location)

    def query(self, locations, query_boundary, found_locations):
        if not self.boundary.intersects(query_boundary):
            return

        location_ids = json.loads(self.location_ids)
        for location_id in location_ids:
            location = locations.get(id=location_id)
            if query_boundary.contains(location):
                found_locations.append(location)

        if self.divided:
            self.child_nw.query(locations, query_boundary, found_locations)
            self.child_ne.query(locations, query_boundary, found_locations)
            self.child_sw.query(locations, query_boundary, found_locations)
            self.child_se.query(locations, query_boundary, found_locations)


class User(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "user"


class Location(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        db_table = "location"
