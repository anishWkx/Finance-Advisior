from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_document(
    extracted_sections,
    source_filename,
    file_type
):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = []

    for section_index, section in enumerate(extracted_sections):

        text = section.get("content", "")

        if not text.strip():
            continue

        text_chunks = splitter.split_text(text)

        for chunk_index, chunk_text in enumerate(text_chunks):

            metadata = {
                "source": source_filename,
                "file_type": file_type,
                "section": section_index + 1,
                "chunk_index": chunk_index
            }

            if "page" in section:
                metadata["page"] = section["page"]

            if "sheet" in section:
                metadata["sheet"] = section["sheet"]

            chunks.append({
                "content": chunk_text,
                "metadata": metadata
            })

    return chunks
