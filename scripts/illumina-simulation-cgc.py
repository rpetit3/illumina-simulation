#! /usr/bin/env python3
# A wrapper for staphopia.nf, mainly for use on CGC.
import logging
import os
import subprocess
from Bio import Entrez
Entrez.email = 'robert.petit@emory.edu'
DATABASE = 'nucleotide'
RETTYPE = 'fasta'
RETMODE = 'text'




def output_handler(output, redirect='>'):
    if output:
        return [open(output, 'w'), '{0} {1}'.format(redirect, output)]
    else:
        return [subprocess.PIPE, '']


def onfinish_handler(cmd, out, err, returncode):
    out = '\n{0}'.format(out) if out else ''
    err = '\n{0}'.format(err) if err else ''
    if returncode != 0:
        logging.error('COMMAND: {0}'.format(cmd))
        logging.error('STDOUT: {0}'.format(out))
        logging.error('STDERR: {0}'.format(err))
        logging.error('END\n'.format(err))
        raise RuntimeError(err)
    else:
        logging.info('COMMAND: {0}'.format(cmd))
        logging.info('STDOUT: {0}'.format(out))
        logging.info('STDERR: {0}'.format(err))
        logging.info('END\n'.format(err))
        return [out, err]


def byte_to_string(b):
    if b:
        return b.decode("utf-8")
    else:
        return ''


def run_command(cmd, cwd=os.getcwd(), stdout=False, stderr=False):
    """Execute a single command and return STDOUT and STDERR."""
    stdout, stdout_str = output_handler(stdout)
    stderr, stderr_str = output_handler(stderr, redirect='2>')

    p = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, cwd=cwd)

    out, err = p.communicate()
    return onfinish_handler(
        '{0} {1} {2}'.format(' '.join(cmd), stdout_str, stderr_str),
        byte_to_string(out), byte_to_string(err), p.returncode
    )


def generate_nextflow(name, fasta, replicate, resume):
    cmd = ['./illumina-simulation.nf', '--name', name, '--fasta', fasta,
           '--coverages', '/opt/data/cgc-coverages.txt',
           '--replicate', replicate]

    if resume:
        cmd.append('-resume')

    return cmd


if __name__ == '__main__':
    import argparse as ap

    parser = ap.ArgumentParser(
        prog='illumina-simulation-ncbi.py',
        conflict_handler='resolve',
        description=('A wrapper for executing Illumina Simualtion.'))
    parser.add_argument('accession', metavar="ACCESSION", type=str,
                        help=('NCBI accession to retrieve reference FASTA'))
    parser.add_argument(
        '--replicate', metavar="INT", type=str, default="1",
        help='Replicate number for random seed generation (Default 1)'
    )
    parser.add_argument('--resume', action='store_true', default=False,
                        help='Tell nextflow to resume the run.')

    args = parser.parse_args()
    name = args.accession
    outdir = '{0}/{1}'.format(os.getcwd(), args.accession)

    # Setup logs
    logging.basicConfig(filename='{0}-simulation.txt'.format(args.accession),
                        filemode='w', level=logging.INFO)

    # Make directory
    run_command(['mkdir', '-p', args.accession])

    # Download FASTA
    fasta = '{0}/{1}/{1}.fasta'.format(os.getcwd(), args.accession)
    with open(fasta, 'w') as fasta_handle:
        efetch = Entrez.efetch(db=DATABASE, id=args.accession,
                               rettype=RETTYPE, retmode=RETMODE)
        fasta_handle.write(efetch.read())
        efetch.close()

    # Run pipeline
    run_command(['cp', '/usr/local/bin/illumina-simulation.nf', outdir])
    nextflow = generate_nextflow(
        args.accession, fasta, args.replicate, args.resume
    )
    run_command(nextflow, cwd=outdir)

    # Tarball and delete directory.nextflow.log
    tarball = '{0}-simulation.tar'.format(args.accession)
    run_command(['rm', '-rf', "{0}/.nextflow/".format(outdir)])
    run_command(['rm', '-rf', "{0}/.nextflow.log".format(outdir)])
    run_command(['rm', '-rf', "{0}/illumina-simulation.nf".format(outdir)])
    run_command(['tar', '-cvf', tarball, args.accession])
    run_command(['gzip', '-f', '--fast', tarball])
    run_command(['rm', '-rf', outdir])
