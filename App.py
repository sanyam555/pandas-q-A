import streamlit as st
from query import answer_question
from fix_code import fix_code

st.set_page_config(page_title="Pandas RAG Assistant", page_icon="🐼", layout="wide")
st.title("Pandas RAG Assistant")

tab1, tab2 = st.tabs(["Ask a question", "Fix my code"])

with tab1:
    st.subheader("Ask a pandas question")
    question = st.text_input("Your question:", placeholder="How do I group by a column and compute the mean?")

    if st.button("Ask", key="ask_button") and question:
        with st.spinner("Retrieving docs and generating an answer..."):
            result = answer_question(question)

        st.markdown("### Answer")
        st.write(result["answer"])

        if result["code"]:
            st.markdown("### Generated code")
            st.code(result["code"], language="python")

            st.markdown("### Execution result")
            exec_result = result["execution_result"]
            if exec_result["success"]:
                st.success("Code ran successfully")
                if exec_result["output"]:
                    st.code(exec_result["output"], language="text")
            else:
                st.error("Code failed to run")
                st.code(exec_result["error"], language="text")

        with st.expander("Show retrieved source passages"):
            for i, doc in enumerate(result["docs"], start=1):
                st.markdown(f"**[{i}] {doc.metadata['title']}**")
                st.text(doc.page_content[:500] + "...")

with tab2:
    st.subheader("Fix broken pandas code")
    broken_code = st.text_area("Paste your broken code:", height=150,
                                 placeholder="df.groupby('cty')['score'].mean()")

    if st.button("Fix it", key="fix_button") and broken_code:
        with st.spinner("Running your code, finding the error, and generating a fix..."):
            result = fix_code(broken_code)

        if result["already_worked"]:
            st.success("Your code already works! Nothing to fix.")
        else:
            st.markdown("### The error your code produced")
            st.code(result["original_error"], language="text")

            st.markdown("### Explanation and fix")
            st.write(result["answer"])

            st.markdown("### Fixed code")
            st.code(result["fixed_code"], language="python")

            st.markdown("### Did the fix work?")
            exec_result = result["fix_execution_result"]
            if exec_result["success"]:
                st.success("Fix works")
                if exec_result["output"]:
                    st.code(exec_result["output"], language="text")
            else:
                st.error("Fix still fails")
                st.code(exec_result["error"], language="text")

            with st.expander("Show retrieved source passages"):
                for i, doc in enumerate(result["docs"], start=1):
                    st.markdown(f"**[{i}] {doc.metadata['title']}**")
                    st.text(doc.page_content[:500] + "...")