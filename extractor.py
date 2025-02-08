# extractor.py
import tarfile

def iter_sentences(tar_filename):
    """
    Generator that yields (sentence_id, lang, text) for each line in the sentences file.
    It opens the tar archive, finds the file whose basename starts with "sentences",
    and streams through its lines.
    """
    with tarfile.open(tar_filename, "r:bz2") as tar:
        member = None
        for m in tar.getmembers():
            # In case the file is inside a folder, check the basename
            if m.name.split("/")[-1].startswith("sentences"):
                member = m
                break
        if member is None:
            raise Exception("Could not find the sentences file in the archive.")
        f = tar.extractfile(member)
        if f is None:
            raise Exception("Could not extract the sentences file.")
        for line in f:
            parts = line.decode('utf-8').rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            yield parts[0], parts[1], parts[2]

def iter_links(tar_filename):
    """
    Generator that yields (sentence_id, translation_id) for each line in the links file.
    It opens the tar archive, finds the file whose basename starts with "links",
    and streams through its lines.
    """
    with tarfile.open(tar_filename, "r:bz2") as tar:
        member = None
        for m in tar.getmembers():
            if m.name.split("/")[-1].startswith("links"):
                member = m
                break
        if member is None:
            raise Exception("Could not find the links file in the archive.")
        f = tar.extractfile(member)
        if f is None:
            raise Exception("Could not extract the links file.")
        for line in f:
            parts = line.decode('utf-8').rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            yield parts[0], parts[1]
