import streamlit as st
from questions import QUESTIONS
from src.auth.auth import authenticate_user
from src.data.storage import (
    save_answer,
    get_user_answers,
    get_last_answered_question,
    save_playground_interaction,
    get_playground_interactions,
)
from src.ui.components import (
    display_question,
    display_navigation,
    display_progress,
    display_answer_history,
    display_playground_history,
)
from src.ai.playground import get_ai_response


def main():
    # Initialize session state
    if "current_question" not in st.session_state:
        st.session_state.current_question = 0
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
        st.session_state.user_email = None

    # Authentication - only show if not authenticated
    if not st.session_state.is_authenticated:
        email = st.text_input("Enter your email address:")
        password = st.text_input("Enter password:", type="password")

        is_authenticated, auth_message = authenticate_user(email, password)
        if is_authenticated:
            st.session_state.is_authenticated = True
            st.session_state.user_email = email
            st.rerun()  # Rerun to refresh the page without login fields
        else:
            st.warning(auth_message)
            return

    # Use stored email for all subsequent operations
    email = st.session_state.user_email

    # AI Settings in sidebar
    with st.sidebar:
        st.markdown("### AI Settings")
        # AI assistance selector
        ai_assistance = st.radio(
            "Select AI Assistance Level:",
            ["No AI Assistance", "GPT-3.5-turbo", "GPT-4o"],
            key=f"ai_assistance_{st.session_state.current_question}",
        )

        # AI Playground
        if ai_assistance != "No AI Assistance":
            st.markdown("### AI Playground")
            prompt = st.text_area(
                "Enter your prompt:",
                height=100,
                key=f"prompt_{st.session_state.current_question}",
                value="",
            )

            if st.button("Run", key=f"run_{st.session_state.current_question}"):
                if not prompt.strip():
                    st.error("Please enter a prompt")
                else:
                    try:
                        response_text, parameters = get_ai_response(
                            prompt, ai_assistance
                        )
                        st.markdown("### Response:")
                        st.write(response_text)

                        save_playground_interaction(
                            email,
                            st.session_state.current_question,
                            prompt,
                            parameters,
                            response_text,
                        )
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # Main content
    st.title("Berkeley Haas: AI For Business Leaders (EWMBA295T.6)")

    # Get the last answered question for this user
    last_answered = get_last_answered_question(email)

    # Navigation
    nav_action = display_navigation(
        st.session_state.current_question, len(QUESTIONS), last_answered
    )
    if nav_action == "previous":
        st.session_state.current_question -= 1
        st.rerun()
    elif nav_action == "next":
        st.session_state.current_question += 1
        st.rerun()

    # Display current question
    current_question = QUESTIONS[st.session_state.current_question]
    display_question(current_question)

    # Get existing answer if any
    existing_answers = get_user_answers(email)
    current_answer = ""
    if not existing_answers.empty:
        answer_row = existing_answers[
            existing_answers["question_number"] == st.session_state.current_question
        ]
        if not answer_row.empty:
            current_answer = answer_row.iloc[0]["answer"]

    # Answer input
    answer = st.text_area(
        "Your Answer:",
        value=current_answer,
        height=200,
        key=f"answer_input_{st.session_state.current_question}",
    )

    if st.button("Submit Answer"):
        if answer.strip():
            if st.session_state.current_question <= last_answered + 1:
                save_answer(email, st.session_state.current_question, answer)
                st.success("Answer submitted successfully!")

                # Check if this was the last question
                if st.session_state.current_question == len(QUESTIONS) - 1:
                    st.balloons()  # Add a celebratory effect
                    st.success(
                        "🎉 Congratulations! You have completed all questions. Thank you for your participation!"
                    )
                # If not the last question, proceed as before
                elif st.session_state.current_question < len(QUESTIONS) - 1:
                    if (
                        f"answer_input_{st.session_state.current_question + 1}"
                        in st.session_state
                    ):
                        del st.session_state[
                            f"answer_input_{st.session_state.current_question + 1}"
                        ]
                    if (
                        f"prompt_{st.session_state.current_question + 1}"
                        in st.session_state
                    ):
                        del st.session_state[
                            f"prompt_{st.session_state.current_question + 1}"
                        ]
                    st.session_state.current_question += 1
                    st.rerun()
            else:
                st.error("Please answer the questions in order.")
        else:
            st.error("Please provide an answer before submitting.")

    # Show progress
    display_progress(last_answered, len(QUESTIONS))


if __name__ == "__main__":
    main()
