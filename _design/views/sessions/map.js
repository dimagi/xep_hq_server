function(doc) {
    if(doc.doc_type == "HQSession" && doc.active == true) {
        emit(doc.key, doc);
    }
}