#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Import all necessary libraries.
"""

import collections
import numpy as np
from os.path import isfile
from statistics import median

"""
Setting up all functions needed 
"""
def breadth_first_search(graph, root):
    visited, queue = {root: 0}, collections.deque([root])
    while queue:
        #why popleft?
        #to represent the FIFO policy of the queue, otherwise a depth_first_search
        #would have been performed
        vertex = queue.popleft()
        for neighbour in graph.neighbors(vertex):
            if neighbour not in visited:
                visited[neighbour] = visited[vertex] + 1
                queue.append(neighbour)
    return visited

def filterEdges(edge,set_of_nodes):
    return edge[0] in set_of_nodes and edge[1] in set_of_nodes          
      
def filter_nodes_in_categories(list_of_articles, set_of_nodes):
    #the following code line computes the intersection between the list of articles into the specific
    #category and the set of nodes in the graph, then recompute the string representation through a join
    #operation.
    return " ".join(list(map(str, list(set.intersection(set(map(int, list_of_articles.strip().split(" "))), set_of_nodes)))))

def computeCategoryDistance(c0, c1, graph, categories):
    #add a fake node pointing to all these articles
    fake_node = "fake_node"
    #retrieve the list of all the articles of the input category
    articles_input_category = list(map(int, categories.iloc[c0]["List_of_articles"].split(" ")))
    #for each article in the input category, a fake edge that goes from the fake_node
    #to each article is created
    for article in articles_input_category:
        graph.add_edge(fake_node, article)
    
    #computing the distances between the fake_node and all the other nodes in the graph
    distances = breadth_first_search(graph, fake_node)
    #delete the fake node after all the distances have been found
    graph.remove_node(fake_node)
    
    #computing the distance between the toy category and another category
    articles_output_category = list(map(int, categories.iloc[c1]["List_of_articles"].split(" ")))
    #this variable will store the shortest path distance values
    list_of_distances = list()
    #for each node in the output category
    for node in articles_output_category:
        #if this node doesn't belong to the input category and if
        #the node is reachable from the input category
        if node not in articles_input_category and node in distances:
            #it is needed to store the distance minus 1, because you don't have
            #to count the edge between the fake_node and the category of interest
            list_of_distances.append(distances[node] - 1)
    #the final distance between the category c0 and c1 is the median of the shortest path distance values
    return median(list_of_distances)

def computeBlockRanking(c0, category_distances):
    #get the row of the distances from c0 to all the others
    distances_input = category_distances[c0]
    #return the array representing the index sorting
    #For instance:
    #distances_input = [1,0,3,2,2]
    #np.argsort(distances_input) = [1,0,3,4,2]
    return np.argsort(distances_input)

def retrieveCategoryDistances(categories, final_graph ,filename = "category_distances.npy"):
    #if the file already exists then it will be loaded from the filesystem
    if isfile("./data/"+filename):
        return np.load("./data/"+filename)
    #otherwise it will be computed and sequently saved on the filesystem
    #let's compute the distance between all the pairs category, store it on the filesystem
    #to not compute the category distance online.
    #
    #initialize a zero-filled matrix to store the distances
    category_distances = np.zeros(shape = (categories.shape[0],categories.shape[0]))
    for i in range(categories.shape[0]):
        for j in range(categories.shape[0]):
            if i != j:
                category_distances[i][j] = computeCategoryDistance(i,j,final_graph,categories)
    np.save("./data/"+filename , category_distances)
    return

#this function aims to compute the final node ranking requested by the RQ2
#it takes as input the whole graph, the block ranking vector and the categories dictionary
def compute_nodes_ranking(allGraph, block_ranking, categories):
    #list that will contain all the nodes in the graph
    final_ranking = list()
    input_category = block_ranking[0]
    graph = allGraph.subgraph(categories[input_category])
    rank_input = dict(graph.in_degree())
    
    for x in reversed(sorted(rank_input, key = rank_input.get)):
        final_ranking.append(x)
    
    for category in block_ranking[1:]:
        #retrieve node of that category
        nodes_category = set(categories[category])
        #retreve the current nodes of the graph
        curr_nodes = set(graph.nodes())
        #compute the union
        new_nodes = set.union(nodes_category, curr_nodes)
        #compute the new subgraph
        graph = allGraph.subgraph(new_nodes)
        for node in rank_input:
            for edge in graph.out_edges(node):
                graph[edge[0]][edge[1]]['weight'] = rank_input[edge[0]]
        tmp = dict(graph.in_degree(weight = 'weight'))
        #delete all nodes that belongs to the already analyzed categories
        toDel = list()
        for key in tmp:
            if key in curr_nodes:
                toDel.append(key)
        for key in toDel:
            del tmp[key]
        rank_input = {**rank_input,**tmp}
        for x in reversed(sorted(tmp, key = tmp.get)):
            final_ranking.append(x)  
    
    if len(final_ranking) >= 10:
        print("The top-10 ranked articles are the following: ")
        print(" ".join([str(x) for x in final_ranking[:10]]))
        print("The entire ranking is saved on the filesystem")
        with open('ranking_'+str(input_category)+'.txt', 'w') as file:
            for node in final_ranking:
                file.write("%i\n" % node)
    else:
        print(" ".join([str(x) for x in final_ranking]))
