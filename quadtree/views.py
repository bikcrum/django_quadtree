from django.shortcuts import render
from django.http import HttpResponse, Http404
import json
from .models import QuadTree, User, Location, Rectangle
import random
from time import time
import string


def sync(request):
    quadtree = QuadTree.objects.first()
    locations = Location.objects.all()

    start_time = time()

    # if there is no record create new quadtree and save it
    if quadtree == None:
        boundary = Rectangle(x=-180, y=-90, w=360, h=180)
        boundary.save()
        quadtree = QuadTree(boundary=boundary)

    for location in locations:
        quadtree.insert(location)

    print('it took', str(time() - start_time), 'to insert/process', str(len(locations)), 'locations')

    return visual(request)


def clear(request):
    User.objects.all().delete()
    Location.objects.all().delete()
    QuadTree.objects.all().delete()
    Rectangle.objects.all().delete()

    return visual(request)


def create_random_user(request, count=1):
    print('creating', count, 'users')
    # create user with random name
    for _ in range(count):
        name = ''.join(random.choices(string.ascii_lowercase, k=5))
        user = User(name=name)
        user.save()

        # create random location
        lat = random.random() * 90 * ((-1) ** random.randint(0, 1))
        lng = random.random() * 180 * ((-1) ** random.randint(0, 1))
        location = Location(user=user, latitude=lat, longitude=lng)
        location.save()

        # get existing quadtree
        quadtree = QuadTree.objects.first()

        # if there is no any quadtree create new
        if quadtree == None:
            boundary = Rectangle(x=-180, y=-90, w=360, h=180)
            boundary.save()
            quadtree = QuadTree(boundary=boundary)

        print(quadtree.__dict__)

        quadtree.insert(location)

    return visual(request)


def visual(request):
    locations = Location.objects.all()
    boundaries = Rectangle.objects.all()
    context = {'locations': locations, 'boundaries': boundaries}
    return render(request, 'quadtree/index.html', context)


def get_nearby_users_using_quadtree(request):
    quadtree = QuadTree.objects.first()
    locations = Location.objects.all()
    if quadtree == None:
        raise Http404('Either there are no any user or you forgot to call quadtree/sync')

    if request.is_ajax():
        if request.method == 'POST':
            request_json = json.loads(request.body.decode('utf-8'))

            latitude = request_json['latitude']
            longitude = request_json['longitude']

            found_locations = []

            start_time = time()

            query_boundary = Rectangle(x=longitude - 20, y=latitude - 20, w=40, h=40)
            quadtree.query(locations=locations, query_boundary=query_boundary,
                           found_locations=found_locations)

            time_taken = time() - start_time

            found_locations = [{"lat": found_location.latitude, "lng": found_location.longitude} for
                               found_location in found_locations]
            print(found_locations)

            return HttpResponse(json.dumps({"data": found_locations,
                                            "meta": {"time_taken": time_taken, "found_locations": len(found_locations),
                                                     "total_locations": locations.count(), "using_quadtree": True}}),
                                content_type='applications/json')

    raise Http404('Something went wrong')


def get_nearby_users(request):
    locations = Location.objects.all()
    if locations.count() == 0:
        raise Http404('There is no any location')

    if request.is_ajax():
        if request.method == 'POST':
            request_json = json.loads(request.body.decode('utf-8'))

            latitude = request_json['latitude']
            longitude = request_json['longitude']
            use_quadtree = request_json['use_quadtree']

            if use_quadtree:
                return get_nearby_users_using_quadtree(request)

            found_locations = []

            start_time = time()

            query_boundary = Rectangle(x=longitude - 20, y=latitude - 20, w=40, h=40)

            for location in locations:
                if query_boundary.contains(location):
                    found_locations.append({"lat": location.latitude, "lng": location.longitude})

            time_taken = time() - start_time

            print(found_locations)

            return HttpResponse(json.dumps({"data": found_locations,
                                            "meta": {"time_taken": time_taken, "found_locations": len(found_locations),
                                                     "total_locations": locations.count(), "using_quadtree": False}}),
                                content_type='applications/json')

    raise Http404('Something went wrong')
