from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from django.core.files.storage import FileSystemStorage
private_storage = FileSystemStorage(location=settings.BASE_DIR+"/private-media/", base_url='/private-media/')

from wildlifecompliance.doctopdf import create_infringement_notice_pdf_contents, create_letter_of_advice_pdf_contents, \
    create_caution_notice_pdf_contents, create_remediation_notice_pdf_contents


def create_infringement_notice_pdf(filename, sanction_outcome):
    value = create_infringement_notice_pdf_contents(filename, sanction_outcome)
    content = ContentFile(value)

    # START: Save the pdf file to the database
    document = sanction_outcome.documents.create(name=filename)
    document._file.save(filename, content, save=False)
    document.save(path_to_file='wildlifecompliance/{}/{}/documents/'.format(sanction_outcome._meta.model_name, sanction_outcome.id))
    # END: Save

    return document


def create_caution_notice_pdf(filename, sanction_outcome):
    value = create_caution_notice_pdf_contents(filename, sanction_outcome)
    content = ContentFile(value)

    # START: Save the pdf file to the database
    document = sanction_outcome.documents.create(name=filename)
    document._file.save(filename, content, save=False)
    document.save(path_to_file='wildlifecompliance/{}/{}/documents/'.format(sanction_outcome._meta.model_name, sanction_outcome.id))
    # END: Save

    return document


def create_letter_of_advice_pdf(filename, sanction_outcome):
    value = create_letter_of_advice_pdf_contents(filename, sanction_outcome)
    content = ContentFile(value)

    # START: Save the pdf file to the database
    document = sanction_outcome.documents.create(name=filename)
    document._file.save(filename, content, save=False)
    document.save(path_to_file='wildlifecompliance/{}/{}/documents/'.format(sanction_outcome._meta.model_name, sanction_outcome.id))
    # END: Save

    return document


def create_remediation_notice_pdf(filename, sanction_outcome):
    value = create_remediation_notice_pdf_contents(filename, sanction_outcome)
    content = ContentFile(value)

    # START: Save the pdf file to the database
    document = sanction_outcome.documents.create(name=filename)
    document._file.save(filename, content, save=False)
    document.save(path_to_file='wildlifecompliance/{}/{}/documents/'.format(sanction_outcome._meta.model_name, sanction_outcome.id))
    # END: Save

    return document
