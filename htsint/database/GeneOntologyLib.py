#!/usr/bin/env python
"""
library of functions for use with the GeneOntology class
"""

import os,sys,re
from htsint import __basedir__

sys.path.append(__basedir__)
try:
    from configure import CONFIG
except:
    CONFIG = None

def get_ontology_file():
    """
    check for presence of ontology file
    raise exception when not found
    return the file path
    """

    if CONFIG == None:
        raise Exception("You must create a configure.py before GeneOntology")

    dataDir = CONFIG['data']

    ontologyFile = os.path.join(dataDir,'go.obo')
    if os.path.exists(ontologyFile) == False:
        raise Exception("Could not find 'go.obo' -- did you run FetchDbData.py?")

    return ontologyFile

def read_ontology_file():
    """
    read the ontology file to find term-term edges
    store all the relationships in a dictionary
    """

    ontologyFile = get_ontology_file()
    fid = open(ontologyFile,'r')
    termCount = 0
    goId = None
    goDict = {"cellular_component":{},
              "molecular_function":{},
              "biological_process":{}}

    def add_term(goNamespace,source,sink):
        if len(sink) != 1 or source == sink[0]:
            return
        if not re.search("GO\:",source) or not re.search("GO\:",sink[0]):
            raise Exception("Invalid go id in ontology file: %s, %s"%(source,sink[0]))

        if goDict[goNamespace].has_key(source) == False:
            goDict[goNamespace][source] = set([])
        goDict[goNamespace][source].update(sink)

    for linja in fid.readlines():
        linja = linja[:-1]

        ## find go id
        if re.search("^id\:",linja):
            goId = re.sub("^id\:|\s+","",linja)
            goName,goNamespace = None,None
            is_a,part_of = None,None
            isObsolete = False
            termCount += 1
            continue 

        ## find a few go id attributes
        if re.search("^name\:",linja):
            goName = re.sub("^name\:\s+","",linja)
        if re.search("^namespace\:",linja):
            goNamespace = re.sub("^namespace\:\s+","",linja)
        if re.search("^def\:",linja):
            goDef = re.sub("^def\:\s+","",linja)
            if re.search("OBSOLETE\.",goDef):
                isObsolete = True

        ## ignore obolete terms
        if goId == None or isObsolete == True:
            continue

        ## add term relationships (is_a)
        if re.search("^is\_a\:",linja):
            is_a = re.sub("^is\_a\:\s+","",linja)
            is_a_sink = re.findall("GO\:\d+",is_a)
            add_term(goNamespace,goId,is_a_sink)

        ## other term relationships
        #if re.search("^relationship\:",linja):
        #    part_of_sink = re.findall("GO\:\d+",linja)
        #    add_term(goNamespace,goId,part_of_sink)
            
    return goDict

def get_idmapping_file():
    """
    check for presence of the annotation file
    raise exception when not found
    return the file path
    """

    if CONFIG == None:
        raise Exception("You must create a configure.py before GeneOntology")

    dataDir = CONFIG['data']
    idmappingFile = os.path.join(dataDir,'idmapping.tb.db')
    if os.path.exists(idmappingFile) == False:
        raise Exception("Could not find 'idmapping.tb.db' -- did you run FetchDbData.py?")

    return idmappingFile

    
def get_annotation_file():
    """
    check for presence of the annotation file
    raise exception when not found
    return the file path
    """

    if CONFIG == None:
        raise Exception("You must create a configure.py before GeneOntology")

    dataDir = CONFIG['data']

    annotationFile = os.path.join(dataDir,'gene_association.goa_uniprot_noiea.db')
    if os.path.exists(annotationFile) == False:
        raise Exception("Could not find 'go.obo' -- did you run FetchGo.py?")

    return annotationFile

    
def read_annotation_file():
    """
    read the annotation file into a dictionary
    This will take some time
    This function is intended for use with database population

    http://www.geneontology.org/GO.format.gaf-2_0.shtml
    """

    annotationFile = get_annotation_file()
    annotationFid = open(annotationFile,'rU')
    result = {}

    for record in annotationFid:
        record = record[:-1].split("\t")

        ## check that it is a uniprot entry
        if record[0][0] == "!":
            continue
        
        dbObjectId = record[1]
        dbObjectSymbol = record[2]
        goID = record[4]
        dbReference = record[5]
        evidenceCode = record[6]
        aspect = record[8]
        dbObjectType = record[11]
        taxon = re.sub("taxon:","",record[12])
        date = record[13]
        assignedBy = record[14]

        ## ignore annotations with multiple species
        if re.search("\|",taxon):
            continue

        if not result.has_key(dbObjectId):
            result[dbObjectId] = {'names':set([]),'annots':{},'taxon':taxon}

        result[dbObjectId]['annots'][goID] = [aspect,evidenceCode]
        result[dbObjectId]['names'].update([dbObjectSymbol])

    annotationFid.close()
    return result
