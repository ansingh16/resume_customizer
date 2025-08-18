import re 

class ResumeModifier:
    """ 
    A class to handle modifications to a LaTeX resume file.
    It can extract sections from the resume, modify them, and save the changes back to the file.
    
    Attributes:
        resume_path (str): The path to the LaTeX resume file.
        job_description (str): The path to the job description file.

    """

    def __init__(self, resume_path, job_description=None):
        # Initialize the ResumeModifier with the path to the LaTeX resume file.
        self.resume_path = resume_path
        # check if the file exists
        try:
            with open(self.resume_path, 'r') as file:
                self.resume_content = file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"The file {self.resume_path} does not exist.")
        
        # job description file
        self.job_description = job_description
        if self.job_description:
            try:
                with open(self.job_description, 'r') as file:
                    self.job_description_content = file.read()
            except FileNotFoundError:
                raise FileNotFoundError(f"The job description file {self.job_description} does not exist.")
        else:
            self.job_description_content = None


    def extract_intro_and_sections(self):
        """
        Extract the personal info / intro and the sections separately from a LaTeX resume.
        Returns:
            intro: str (personal info at top)
            sections: list of strings (each LaTeX section)
        """
        
        # Everything between \begin{document} and \end{document}
        body_start = self.resume_content.split("\\begin{document}", 1)[1]
        body, _, _ = body_start.partition("\\end{document}")

        # Split into intro (everything before first section) and sections
        match = re.search(r"\\section\*?|\\section", body)
        if not match:
            raise ValueError("No sections found in resume.")

        intro = body[:match.start()].strip()  # personal info
        sections_text = body[match.start():]

        # Split sections by \section or \section*
        sections = re.split(r"(?=\\section\*?|\\section)", sections_text)
        sections = [sec.strip() for sec in sections if sec.strip()]

        self.intro = intro
        self.sections = sections

    
    def assemble_resume(self,tailored_sections, output_file="tailored_resume.tex"):
        """
        Reassemble LaTeX resume keeping preamble, intro (personal info), and modified sections.
        """
        

        preamble, _, _ = self.resume_content.partition("\\begin{document}")
        _, sep, end = self.resume_content.rpartition("\\end{document}")
        end_document = sep + end if sep else "\\end{document}"

        # Join sections safely
        new_content = preamble + "\\begin{document}\n\n" + self.intro + "\n\n" + "\n\n".join(tailored_sections) + "\n\n" + end_document

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"Tailored resume saved to {output_file}")
