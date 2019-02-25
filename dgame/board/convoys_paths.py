

def __get_convoy_paths(start_location, max_convoy_length, queue):
    """ Returns a list of possible convoy destinations with the required units to get there
        Does a breadth first search from the starting location

        :param map_object: The instantiated map
        :param start_location: The start location of the unit (e.g. 'LON')
        :param max_convoy_length: The maximum convoy length permitted
        :param queue: Multiprocessing queue to display the progress bar
        :return: A list of ({req. fleets}, {reachable destinations})
        :type map_object: diplomacy.Map
    """
    from queue import Queue

    to_check = Queue()  # Items in queue have format ({fleets location}, last fleet location)
    dest_paths = {}  # Dict with dest as key and a list of all paths from start_location to dest as value

    # We need to start on a coast / port
    sloc = start_location
    if len(sloc.seas) == 0 or sloc.is_water:
        return []

    # Queuing all adjacent water locations from start
    for tile in sloc.seas:
        to_check.put(({tile}, tile))

    # Checking all subsequent adjacencies until no more adjacencies are possible
    while not to_check.empty():
        fleets_loc, last_loc = to_check.get()

        # Checking adjacencies
        for loc in last_loc.neighbours:  # type: Province

            # If we find adjacent coasts, we mark them as a possible result
            # if map_object.area_type(loc) in ('COAST', 'PORT') and '/' not in loc and loc != start_location:
            if not loc.is_water and loc.without_coast is not sloc:
                dest_paths.setdefault(loc.without_coast, [])

                # If we already have a working path that is a subset of the current fleets, we can skip
                # Otherwise, we add the new path as a valid path to dest
                for path in dest_paths[loc.without_coast]:
                    if path.issubset(fleets_loc):
                        break
                else:
                    dest_paths[loc.without_coast] += [fleets_loc]

            # If we find adjacent water/port, we add them to the queue
            elif loc.is_water and loc not in fleets_loc and len(fleets_loc) < max_convoy_length:
                to_check.put((fleets_loc | {loc}, loc ))

    # Merging destinations with similar paths
    similar_paths = {}
    for dest, paths in dest_paths.items():
        for path in paths:
            tuple_path = tuple(sorted(path))
            similar_paths.setdefault(tuple_path, set([]))
            similar_paths[tuple_path] |= {dest.without_coast}

    # Converting to list
    results = []
    for fleets, dests in similar_paths.items():
        results += [(start_location, set(fleets), dests)]

    # Returning
    queue.put(1)
    return results


def __display_progress_bar(queue, max_loop_iters):
    """ Displays a progress bar
        :param queue: Multiprocessing queue to display the progress bar
        :param max_loop_iters: The expected maximum number of iterations
    """
    import tqdm
    progress_bar = tqdm.tqdm(total=max_loop_iters)

    for _ in iter(queue.get, None):
        progress_bar.update()

    progress_bar.close()


def build_convoy_paths_cache(map_def, max_convoy_length=25):
    """ Builds the convoy paths cache for a map
        :param map_object: The instantiated map object
        :param max_convoy_length: The maximum convoy length permitted
        :return: A dictionary where the key is the number of fleets in the path and
                 the value is a list of convoy paths (start loc, {fleets}, {dest}) of that length for the map
        :type map_object: diplomacy.Map
    """
    print('Generating convoy paths for {}'.format('-'))
    import multiprocessing
    import threading
    import collections

    coasts = []
    for loc in map_def.PROVINCE_DB:
        if (not loc.is_water and len(loc.seas) > 0) and '/' not in loc.short:
            coasts.append(loc)

    # Starts the progress bar loop
    manager = multiprocessing.Manager()
    queue = manager.Queue()
    progress_bar = threading.Thread(target=__display_progress_bar, args=(queue, len(coasts)))
    progress_bar.start()

    # Getting all paths for each coasts in parallel
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    tasks = [(coast, max_convoy_length, queue) for coast in coasts]
    results = pool.starmap(__get_convoy_paths, tasks)
    pool.close()
    results = [item for sublist in results for item in sublist]
    queue.put(None)
    progress_bar.join()

    # Splitting into buckets
    buckets = collections.OrderedDict({i: [] for i in range(1, len(map_def.PROVINCE_DB) + 1)})
    for start, fleets, dests in results:
        buckets[len(fleets)] += [(start, fleets, dests)]

    # Returning
    print('Found {} convoy paths for {}\n'.format(len(results), ''))
    return buckets
