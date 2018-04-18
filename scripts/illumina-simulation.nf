#!/usr/bin/env nextflow
import groovy.json.JsonSlurper
params.help = null
params.outdir = null
params.fasta = null
params.coverages = null
params.replicate = 1
params.clear_cache_on_success = true
params.clear_logs = true

if (params.help) {
    print_usage()
    exit 0
}

check_input_params()

// Set some global variables
String[] coverages = new File(params.coverages) as String[]
name = params.name
outdir = params.outdir ? params.outdir : './'
replicate = params.replicate

/* ==== START SIMULATION ==== */

process simulate {
    publishDir outdir, mode: 'copy', overwrite: true
    input:
        val coverage from Channel.from(coverages)
        file fasta from Channel.value(file(params.fasta))
    output:
        file '*.fq' into FASTQ
    shell:
        random_seed = (coverage.toFloat() * replicate.toInteger() * 100).round()
        '''
        art_illumina -l 100 -f !{coverage} -na -ss HS20 -rs !{random_seed} \
                     -i !{fasta} -o !{name}-!{coverage}-!{replicate}
        '''
}

process count_kmers {
    publishDir outdir, mode: 'copy', overwrite: true
    input:
        file fq from FASTQ
    output:
        file '*.jf'
    shell:
        jf = fq.name.replaceAll('.fq', '.jf')
        '''
        jellyfish count -C -m 31 -s 1M -o !{jf} !{fq}
        '''
}

/* ==== END SIMULATION ==== */

workflow.onComplete {
    if (workflow.success == true && params.clear_cache_on_success) {
        // No need to resume completed run so remove cache.
        file('./work/').deleteDir()
    }
    println """
    Pipeline execution summary
    ---------------------------
    Completed at: ${workflow.complete}
    Duration    : ${workflow.duration}
    Success     : ${workflow.success}
    workDir     : ${workflow.workDir}
    exit status : ${workflow.exitStatus}
    Error report: ${workflow.errorReport ?: '-'}
    """
}

// Utility Functions
def print_usage() {
    log.info 'Illumina Simulation Pipeline'
    log.info ''
    log.info 'Required Options:'
    log.info '    --fasta     FASTA   Input reference FASTA to simulate'
    log.info '    --name      STR     A name to give the run'
    log.info '    --coverages TXT     A file with coverages to simulate'
    log.info ''
    log.info 'Optional:'
    log.info '    --replicate  INT  Replicate number for random seed generation (Default 1)'
    log.info '    --outdir     DIR  Directory to write results to. (Default ./${NAME})'
    log.info '    --help             Show this message and exit'
    log.info ''
    log.info 'Usage:'
    log.info '    nextflow illumina-simulation --fasta input.fasta --name saureus --coverage 10'
}

def check_input_params() {
    error = false
    if (!params.name) {
        log.info('A name is required to continue. Please use --name')
        error = true
    }

    if (!params.coverages) {
        log.info('A file with coverages to simulate is required to continue. Please use --coverages')
        error = true
    } else if (!file(params.coverages).exists()) {
        log.info('Invailid input (--coverages), please verify "' + params.coverages + '"" exists.')
        error = true
    }

    if (!params.fasta) {
        log.info('A reference FASTA is required. Please use --fasta')
        error = true
    } else if (!file(params.fasta).exists()) {
        log.info('Invailid input (--fasta), please verify "' + params.fasta + '"" exists.')
        error = true
    }

    if (error) {
        log.info('See --help for more information')
        exit 1
    }
}
