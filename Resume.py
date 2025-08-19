import re 
from pathlib import Path
import google.generativeai as genai
import subprocess
import time 
import os
# from dotenv import load_dotenv

# load_dotenv()  # loads .env into environment
# api_key = os.getenv("API_KEY")

# # 🔑 Set your API key once (env variable recommended)
# genai.configure(api_key=api_key)

import ollama 


class ResumeModifier:
    """ 
    A class to handle modifications to a LaTeX resume file.
    It can extract sections from the resume, modify them, and save the changes back to the file.
    
    Attributes:
        resume_path (str): The path to the LaTeX resume file.
        job_description (str): The path to the job description file.

    """

    def __init__(self, resume_path, job_description=None, outdir=None, company_name=None):
        
        # Initialize attributes
        self.tailored_sections = None
        self.intro = None
        self.sections = None

        # Set up the output directory and company name if provided
        if outdir and company_name:
            self._setup(outdir, company_name)
        else:
            self.outdir = None
            self.company_name = None
            self.outfile = None

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
        
        
    def _setup(self,outdir = None, company_name =None):
        """
        Set up the output directory for the tailored resume.
        """
        # make dir
        Path(outdir).mkdir(parents=True, exist_ok=True)
        # set attributes
        self.outdir = outdir
        self.company_name = company_name
        self.outfile = Path(self.outdir) / f"{self.company_name}_resume.tex"

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


    
    def tailor_sections_with_model(self, job_description_file=None, model_name="gemini-2.5-pro", debug=False):
        """
        Reads job description from a file, sends each resume section to Gemini,
        and tailors it accordingly. Returns modified section strings.
        In debug mode, skips Gemini and prints each section.
        """

                
        model_name = "llama3:8b"

        # Prime the model once with the job description
        job_description = open("job_description.txt", "r", encoding="utf-8").read().strip()

        # Create a system prompt to "prime" the model
        system_prompt = f"""
        You are an expert resume editor. 
        The following is the job description to align the resume sections with:
        {job_description}
        Only edit the content of each LaTeX resume section given to you. 
        ONLY return the edited LaTeX content. Do NOT include explanations, summaries, or comments. Keep all LaTeX commands intact.

        """
        tailored_sections = []

        for i, sec in enumerate(self.sections, 1):
            print(f"Tailoring section {i}")
            
            # Use a concise prompt with the section
            prompt = f"{system_prompt}\nResume section:\n{sec}\nEdited section:"

            response = ollama.generate(model=model_name, prompt=prompt)

            
            # Extract the text from the response
            edited_sec = response.get("response", sec)  # fallback to original if empty
            tailored_sections.append(edited_sec)

        self.tailored_sections = tailored_sections
        

        # # Read job description from file
        # job_description = Path(job_description_file).read_text(encoding="utf-8").strip()

        # # Initialize the Generative Model
        # model = genai.GenerativeModel(model_name)

        # # Prime the model with job description once
        # system_prompt = f"""
        # You are an expert resume editor. Tailor the content of resume sections
        # so they better match the following job description.
        # Do NOT change LaTeX commands, only the text.

        # Job description:
        # {job_description}
        # """

        # tailored = []

        # for i, sec in enumerate(self.sections, start=1):

        #     print(f"Processing section {i}/{len(self.sections)}...")
        #     user_prompt = f"Modify this resume section:\n{sec}"
            
        #     response = model.generate_content(
        #         messages=[
        #             {"role": "system", "content": system_prompt},
        #             {"role": "user", "content": user_prompt}
        #         ]
        #     )

        #     if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        #         edited_sec = "".join([part.text for part in response.candidates[0].content.parts if part.text])
        #     else:
        #         edited_sec = sec  # fallback

        #     tailored.append(edited_sec)


        # self.tailored_sections = tailored


   
    def assemble_resume(self):
        """
        Reassemble LaTeX resume keeping preamble, intro (personal info), and modified sections.
        """

        # if no tailored sections, set to original sections
        if self.tailored_sections is None:
            self.tailored_sections = self.sections

        # Extract preamble
        preamble, _, _ = self.resume_content.partition("\\begin{document}")
        _, sep, end = self.resume_content.rpartition("\\end{document}")
        end_document = sep + end if sep else "\\end{document}"

        # Join sections safely
        new_content = preamble + "\\begin{document}\n\n" + self.intro + "\n\n" + "\n\n".join(self.tailored_sections) + "\n\n" + end_document

        
        with open(self.outfile, "w", encoding="utf-8") as f:
            f.write(new_content)

        subprocess.run(["latexmk", "-cd", "-pdf", str(self.outfile)], check=True)

        print(f"Tailored resume saved to {self.outfile}")

    def _clean(self):
        """
        Clean the compiled files generated by latexmk.
        
        This function runs latexmk to clean the compiled files generated by the
        resume assembly process. Specifically, it removes the auxiliary files
        generated during the compilation process.
        
        Parameters:
            None
            
        Returns:
            None
        """
    
        subprocess.run(["latexmk", "-cd", "-c", f"{self.outfile}"], check=True)

    def modify_resume(self,debug=False):
        """
        Main method to modify the resume.
        Extracts sections, tailors them with the model, and assembles the final resume.
        """

        print("Extracting sections from resume...")
        self.extract_intro_and_sections()
        
        # If job description is provided, tailor sections with the model
        print("Tailoring sections with the model...")
        if self.job_description:
            self.tailor_sections_with_model(self.job_description, debug=debug)
        else:
            print("No job description provided. Skipping tailoring.")

        print("Assembling the final resume...")
        self.assemble_resume()
        print("Resume modification complete.")
        self._clean()
        print("Temporary files cleaned up.")