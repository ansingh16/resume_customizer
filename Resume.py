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


    def extract_resume_sections(self):
        """
        Extract only LaTeX resume sections, skipping preamble and personal info.
        Returns a list of sections as strings.
        """
        # Ensure document starts correctly
        if "\\begin{document}" not in self.resume_content:
            raise ValueError("No \\begin{document} found in LaTeX file.")

        # Extract everything after \begin{document}
        body_start = self.resume_content.split("\\begin{document}", 1)[1]

        # Extract everything before \end{document}, if present
        body, sep, after = body_start.partition("\\end{document}")

        # Skip personal info: start from first \section or \section*
        first_section_match = re.search(r"\\section\*?|\\section", body)
        if not first_section_match:
            raise ValueError("No \\section found in LaTeX resume body.")

        sections_text = body[first_section_match.start():]

        # Split by section headers
        sections = re.split(r"(?=\\section\*?|\\section)", sections_text)
        sections = [sec.strip() for sec in sections if sec.strip()]

        return sections