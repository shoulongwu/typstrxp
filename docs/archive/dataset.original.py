"""
Task definitions for Experiment C1: Real-World Scenario Typst Document Generation
10 Real-world Tasks across 5 categories:
  1. Handout Documents (3 tasks):
     - C1_01: Linear Algebra Eigenvalues & Eigenvectors
     - C1_02: Calculus Gauss Divergence Theorem
     - C1_03: Probability Poisson Distribution
  2. Academic Paper Typesetting (2 tasks):
     - C1_04: Double-column Academic Paper on Sigmoid Activation & ML Binary Classification
     - C1_05: Single-column Research Technical Report on Deep Learning Activation Evolution
  3. Resume / Curriculum Vitae (2 tasks):
     - C1_06: Academic Researcher / Postdoc Research CV (2 full pages)
     - C1_07: Senior Full-Stack Distributed Systems Architect Tech Resume (2 full pages)
  4. Final Examination Paper (1 task):
     - C1_08: University Graduate Final Exam Paper in Advanced Matrix Analysis
  5. Commercial Business Reports (2 tasks):
     - C1_09: Enterprise Generative AI Commercial Investment Feasibility Report
     - C1_10: Digital Supply Chain Operations & Financial Strategic Advisory Report
"""

import re

TASKS = [
    # =========================================================================
    # CATEGORY 1: 讲义文档 (Handouts / Lecture Notes) - 3 Tasks
    # =========================================================================
    {
        "id": "C1_01",
        "category": "handout",
        "category_zh": "讲义文档",
        "name": "Linear Algebra: Matrix Eigenvalues & Eigenvectors",
        "name_zh": "线性代数：矩阵特征值与特征向量理论及对角化",
        "target_page_range": (2, 5),
        "prompt_task": """Create a comprehensive, university-level mathematics lecture handout in Typst titled 'Linear Algebra: Eigenvalues, Eigenvectors, and Matrix Diagonalization'.

Document Requirements:
1. Document Setup & Aesthetics:
   - Configure page to A4 with 2.5cm margins and running header ('Advanced Linear Algebra - Lecture Notes') and footer with page numbers.
   - Use structured heading levels (= for Lecture Title, == for Sections, === for Subsections).
   - Use visual blocks or callouts for Definitions, Theorems, and Remarks.

2. Content & Pedagogical Structure (Ensure thorough explanations, no truncated placeholders):
   - Section 1: Geometric Motivation & Core Intuition (Vector transformations, invariant directions, dilation factors).
   - Section 2: Mathematical Foundations (Eigenvalue equation $A v = lambda v$, characteristic polynomial $p(lambda) = det(A - lambda I) = 0$, trace and determinant relations $tr(A) = sum lambda_i$, $det(A) = prod lambda_i$).
   - Section 3: Fundamental Theorems & Rigorous Proofs (State and provide a full, step-by-step mathematical proof for the theorem: 'Eigenvectors corresponding to mutually distinct eigenvalues are linearly independent').
   - Section 4: Matrix Diagonalization Theory (Algebraic multiplicity vs Geometric multiplicity, necessary and sufficient condition for similarity diagonalization $P^(-1) A P = D$).
   - Section 5: Step-by-Step Worked Example (Define an explicit 3x3 matrix, write out characteristic polynomial expansion, compute the 3 eigenvalues, solve the homogeneous systems $(A - lambda I)v = 0$ for eigenvector bases, construct modal matrix $P$, and verify $P^(-1) A P$).
   - Section 6: Spectral Theorem for Real Symmetric Matrices (Orthogonal diagonalization $Q^T A Q = Lambda$).
   - Section 7: Practice Problems & Analytical Exercises (At least 4 structured exercises with varying difficulty).

3. Length Constraint:
   - The compiled document MUST span between 2 and 4 full pages (at least 2 pages, at most 5 pages). Provide full mathematical derivations, descriptive explanatory text, and complete formulas to ensure adequate document length.""",
        "semantic_checker": lambda code: bool(
            re.search(r'(?i)(eigenvalue|eigenvector|特征值|特征向量)', code) and
            re.search(r'(?i)(diagonaliz|对角化|characteristic)', code) and
            ('det(' in code or 'lambda' in code or '$' in code) and
            len(code.splitlines()) >= 50
        ),
    },

    {
        "id": "C1_02",
        "category": "handout",
        "category_zh": "讲义文档",
        "name": "Calculus: Gauss Divergence Theorem & Surface Integrals",
        "name_zh": "高等数学：高斯散度定理、向量场通量与闭合曲面积分",
        "target_page_range": (2, 5),
        "prompt_task": """Create an advanced calculus lecture handout in Typst titled 'Multivariable Calculus: The Gauss Divergence Theorem and Flux Integrals'.

Document Requirements:
1. Document Setup & Layout:
   - Configure page to A4 with elegant margins, running headers ('Multivariable Analysis - Lecture Series'), and page numbering.
   - Use clear hierarchical sectioning and styled callout boxes for definitions and key theorems.

2. Content Requirements (Provide exhaustive, step-by-step mathematical text and derivations):
   - Section 1: Vector Fields & Physical Motivation (Fluid flow, source density, sink density, concept of net outward flux).
   - Section 2: Mathematical Definition of Divergence (Cartesian coordinates: $div F = nabla dot F = (partial P)/(partial x) + (partial Q)/(partial y) + (partial R)/(partial z)$, physical interpretation as local volumetric expansion rate).
   - Section 3: The Gauss Divergence Theorem (Formal mathematical theorem statement: closed surface integral of $F dot d S$ equals volume integral of $div F d V$ over bounded solid Omega, orientation of outward unit normal).
   - Section 4: Analytical Derivation Sketch (Decomposing flux into coordinate projections and applying the Fundamental Theorem of Calculus along slices).
   - Section 5: In-Depth Computational Examples:
     * Example 1: Calculate the flux of $F(x,y,z) = (x, y, z)$ over the unit sphere using both direct surface parameterization and the Divergence Theorem, verifying identical results.
     * Example 2: Calculate outward flux through a closed cylindrical solid bounded by $x^2 + y^2 <= R^2$ and $0 <= z <= h$.
   - Section 6: Physics Connection: Maxwell's First Equation (Gauss's Law for electrostatics, converting between integral and differential forms $nabla dot E = rho / epsilon_0$).
   - Section 7: Critical Pitfalls & Boundary Conditions (Punctured domains, point singularities like $r / ||r||^3$, piecewise smooth boundaries).
   - Section 8: Review Exercises (3 detailed challenge problems with guided hints).

3. Length Constraint:
   - The compiled document MUST span between 2 and 4 full pages (at least 2 pages, at most 5 pages). Ensure extensive narrative explanations, detailed multi-line equations, and comprehensive discussion.""",
        "semantic_checker": lambda code: bool(
            re.search(r'(?i)(gauss|divergence|高斯|散度|flux|通量)', code) and
            re.search(r'(?i)(surface|integral|曲面|积分)', code) and
            ('nabla' in code or 'div' in code or 'integral' in code or 'int' in code or '$' in code) and
            len(code.splitlines()) >= 50
        ),
    },

    {
        "id": "C1_03",
        "category": "handout",
        "category_zh": "讲义文档",
        "name": "Probability Theory: Poisson Distribution & Poisson Processes",
        "name_zh": "概率论与数理统计：泊松分布、极限定理与泊松过程",
        "target_page_range": (2, 5),
        "prompt_task": """Create a rigorous mathematical statistics lecture handout titled 'Probability Theory: The Poisson Distribution, Limit Theorems, and Counting Processes'.

Document Requirements:
1. Document Setup:
   - Configure page to A4, clear headers ('Probability & Statistics Handouts'), footers with page numbering.
   - Employ distinct styled blocks for Definitions, Theorems, Proofs, and Examples.

2. Content Structure (Must be fully written out with full formulas and proofs):
   - Section 1: Historical Context & Modeling Rare Events (Law of small numbers, discrete count phenomena).
   - Section 2: Definition of Poisson Distribution (PMF: $P(X = k) = (lambda^k e^(-lambda)) / k!$, support $k = 0, 1, 2, ...$, proof that total probability sums to 1 using Taylor series).
   - Section 3: Moment Calculations & Characteristics (Complete step-by-step mathematical proof showing $E[X] = lambda$ and $Var(X) = lambda$; derive Moment Generating Function $M_X(t) = exp(lambda (e^t - 1))$).
   - Section 4: The Poisson Limit Theorem (Law of Small Numbers) (Rigorous derivation taking the limit of Binomial PMF as $n -> oo, p -> 0$ with $n p -> lambda$).
   - Section 5: Introduction to Homogeneous Poisson Processes (Stationary independent increments, inter-arrival time distribution being exponential, memoryless property).
   - Section 6: Engineering Applications Comparison Table (Create a Typst table comparing event types, typical rate parameter lambda, observation interval, and variance).
   - Section 7: Worked Case Studies (Detailed numerical solutions for: (a) server network packet drop probability, (b) customer call arrival queue).
   - Section 8: Parameter Estimation (Maximum Likelihood Estimator for lambda from i.i.d. observations, derivation of score function and Fisher information).
   - Section 9: Practice Exercises (4 multi-part exercises with answer keys).

3. Length Constraint:
   - The compiled document MUST span between 2 and 4 full pages (at least 2 pages, at most 5 pages). Provide full mathematical derivations, rich text explanations, tables, and exercises.""",
        "semantic_checker": lambda code: bool(
            re.search(r'(?i)(poisson|泊松|probability|概率)', code) and
            re.search(r'(?i)(distribution|分布|process|过程)', code) and
            ('lambda' in code or 'exp(' in code or '$' in code) and
            len(code.splitlines()) >= 50
        ),
    },

    # =========================================================================
    # CATEGORY 2: 论文排版 (Academic Paper Typesetting) - 2 Tasks
    # =========================================================================
    {
        "id": "C1_04",
        "category": "paper",
        "category_zh": "论文排版",
        "name": "Academic Paper (2-Column): Sigmoid Activation in Machine Learning",
        "name_zh": "学术论文（双栏）：Sigmoid激活函数在机器学习二分类中的数学特性与梯度动力学分析",
        "target_page_range": (2, 5),
        "prompt_task": """Typeset a formal academic research conference paper titled 'Mathematical Dynamics and Gradient Behavior of the Sigmoid Activation Function in Machine Learning Binary Classification'.

Document Requirements:
1. Document Setup & Academic Formatting:
   - Double-column layout (#set page(paper: "a4", columns: 2, margin: (x: 2cm, y: 2.5cm))).
   - Full-width title block across the top, including paper title, authors, institutional affiliations, abstract (150-250 words), and keywords.
   - Numbered sections (= 1. Introduction, == 1.1 Background, etc.).
   - Standard academic typography with mathematical formulas, tables, and formal citations.

2. Content Structure (Substantive content focusing on Sigmoid + Machine Learning):
   - Abstract & Keywords: Binary classification, Sigmoid function, gradient saturation, binary cross-entropy, backpropagation.
   - Section 1: Introduction (Role of nonlinear activations in neural representations, historical prominence of logistic units).
   - Section 2: Analytical Foundations of the Logistic Sigmoid Function (Definition $sigma(z) = 1 / (1 + e^(-z))$, domain, range $(0, 1)$, central symmetry $sigma(-z) = 1 - sigma(z)$, full derivative derivation proving $sigma'(z) = sigma(z)(1 - sigma(z))$, maximum derivative value of 0.25 at $z = 0$).
   - Section 3: Loss Function Coupling & Optimization Dynamics:
     * Coupling with Mean Squared Error (MSE): Showing why MSE induces catastrophic gradient saturation when predictions are confident and wrong.
     * Coupling with Binary Cross-Entropy (BCE): Complete mathematical derivation demonstrating that $partial L_{BCE} / partial z = sigma(z) - y$, resulting in linear error signal and eliminating premature saturation.
   - Section 4: The Vanishing Gradient Problem in Deep Architectures (Chain rule multiplication over $L$ layers: $prod_{l=1}^L sigma'(z_l) <= (1/4)^L$, demonstrating exponential vanishing in deep networks).
   - Section 5: Comparative Empirical Evaluation (Include a Typst table comparing Sigmoid, ReLU, Leaky ReLU, and GELU across Training Loss, Convergence Speed, Gradient Norm at Init, and Classification Accuracy on benchmark datasets).
   - Section 6: Architectural Evolution & Contemporary Applications (Why Sigmoid remains standard for binary classification output layers and gating mechanisms like LSTM/GLU).
   - Section 7: Conclusion & Summary of Findings.
   - References (A bibliography list with at least 6 formal academic citations).

3. Length Constraint:
   - The compiled document MUST span between 2 and 4 full pages (at least 2 pages, at most 5 pages). Fill the paper with comprehensive analytical text, complete equations, tables, and formal references.""",
        "semantic_checker": lambda code: bool(
            re.search(r'(?i)(sigmoid|sigmol|activation|激活函数)', code) and
            re.search(r'(?i)(machine learning|binary classification|机器学习|二分类)', code) and
            ('columns' in code or 'abstract' in code.lower() or 'introduction' in code.lower()) and
            len(code.splitlines()) >= 50
        ),
    },

    {
        "id": "C1_05",
        "category": "paper",
        "category_zh": "论文排版",
        "name": "Academic Survey (1-Column): Deep Learning Activation Evolution from Sigmoid to Modern Units",
        "name_zh": "学术短文/技术报告（单栏）：深度学习激活机制：从Sigmoid到现代自适应非线性变换的演进与实证评估",
        "target_page_range": (2, 5),
        "prompt_task": """Typeset an academic research survey / preprint technical report titled 'From Sigmoid to Adaptive Nonlinearities: A Mathematical Survey of Activation Mechanisms in Deep Learning'.

Document Requirements:
1. Document Setup & Layout:
   - Formal single-column academic technical report (#set page(paper: "a4", margin: (x: 2.5cm, y: 3cm))).
   - Running header ('Technical Report - Deep Learning Non-linearities'), numbered sections, formal table styling.
   - Author, affiliation, abstract, and index terms.

2. Content Structure (Comprehensive machine learning discourse):
   - Abstract & Index Terms.
   - Section 1: Introduction: The Fundamental Role of Non-linear Activation in Deep Representation Learning (Universal Approximation Theorem context).
   - Section 2: The Classical Sigmoidal Family (Logistic Sigmoid, Hyperbolic Tangent $tanh(z) = 2 sigma(2z) - 1$, and Hard-Sigmoid; mathematical equations, plots description, and properties).
   - Section 3: Structural Pathology of Classical Sigmoids (Non-zero-centered outputs causing zig-zagging gradient descent weight updates, asymptotic flat gradients inducing saturation).
   - Section 4: Modern Evolutionary Descendants (Swish / SiLU $f(x) = x sigma(beta x)$, Gated Linear Units (GLU) and SwiGLU in Transformer architectures; equations and gating mechanism formulations).
   - Section 5: Systematic Multi-Dimensional Benchmark Table (Typst table comparing 6 activation functions across: Mathematical Formula, Output Range, Continuity/Smoothness, Computational Cost, Zero-Centering, and Typical Modern Architecture).
   - Section 6: Practical Selection Guidelines for Deep Learning Practitioners (When to use Sigmoid vs ReLU vs SwiGLU across vision, NLP, and tabular tasks).
   - Section 7: Concluding Remarks and Future Horizons.
   - References (At least 8 formal academic bibliography entries).

3. Length Constraint:
   - The compiled document MUST span between 2 and 4 full pages (at least 2 pages, at most 5 pages). Write detailed theoretical analysis, complete mathematical formulations, comprehensive tables, and rich narrative.""",
        "semantic_checker": lambda code: bool(
            re.search(r'(?i)(sigmoid|activation|激活函数)', code) and
            re.search(r'(?i)(deep learning|neural network|深度学习|神经网络)', code) and
            ('table(' in code or 'table.' in code or 'table' in code) and
            len(code.splitlines()) >= 50
        ),
    },

    # =========================================================================
    # CATEGORY 3: 简历 (Resume / Curriculum Vitae) - 2 Tasks
    # =========================================================================
    {
        "id": "C1_06",
        "category": "resume",
        "category_zh": "个人简历",
        "name": "Academic Curriculum Vitae: AI & Machine Learning Researcher",
        "name_zh": "个人简历：人工智能与机器学习博士后/算法科学家学术履历",
        "target_page_range": (2, 5),
        "prompt_task": """Typeset an elegant, professional, two-page academic Curriculum Vitae (CV) for a senior machine learning researcher and postdoctoral fellow.

Document Requirements:
1. Document Setup & Visual Styling:
   - Clean, sophisticated academic styling on A4 paper (#set page(paper: "a4", margin: (x: 2cm, y: 2cm))).
   - Prominent candidate header with Name, Title, Institution, Email, Phone, Google Scholar profile, GitHub, ORCID, and Website.
   - Professional typography with clean divider lines, structured metadata grids, and subtle color accents.

2. Content Structure (Must be dense, complete, and realistic):
   - Executive Research Profile: Core research focus in foundation models, mechanistic interpretability, reasoning dynamics, and mathematical optimization.
   - Education:
     * Ph.D. in Computer Science (Top University, GPA 4.0/4.0, Dissertation Title, Doctoral Advisor, Outstanding Dissertation Award).
     * M.S. in Applied Mathematics (Thesis, High Honors).
     * B.S. in Computer Science & Applied Math (Summa Cum Laude).
   - Academic Appointments: Postdoctoral Research Fellow, Visiting Research Scholar.
   - Selected Peer-Reviewed Publications (Provide 8 complete, realistic bibliographic citations with complete author lists, publication venues across NeurIPS, ICML, ICLR, ACL, JMLR, year, and paper titles).
   - Research Grants & Funded Projects (Grant title, funding agency like NSF, award amount, principal role PI/Co-PI, project scope).
   - Teaching & Mentoring Experience (Instructor of record for Graduate Deep Learning; Teaching Assistant for Linear Algebra; advising 4 graduate students).
   - Academic Service & Professional Activities (Conference Reviewer / Area Chair for NeurIPS, ICML, ICLR; Workshop Organizer).
   - Honors & Fellowships (National Graduate Fellowship, Best Paper Award Nomination, Travel Grants).
   - Technical & Core Competencies (PyTorch, Typst, CUDA, Distributed Training, Python, C++, LaTeX).

3. Length Constraint:
   - The compiled document MUST span EXACTLY 2 pages (or between 2 and 3 full pages, strictly at least 2 pages and at most 5 pages). Format the CV densely with comprehensive publication listings, detailed project descriptions, and academic achievements so that it fully occupies at least 2 pages.""",
        "semantic_checker": lambda code: bool(
            re.search(r'(?i)(curriculum vitae|cv|resume|简历|履历)', code) and
            re.search(r'(?i)(education|publication|research|教育|研究|论文)', code) and
            re.search(r'(?i)(ph\.?d|doctor|master|university|博士|学士)', code) and
            len(code.splitlines()) >= 50
        ),
    },

    {
        "id": "C1_07",
        "category": "resume",
        "category_zh": "个人简历",
        "name": "Professional Tech Resume: Principal Full-Stack Distributed Systems Architect",
        "name_zh": "个人简历：资深全栈软件架构师与系统工程师技术简历",
        "target_page_range": (2, 5),
        "prompt_task": """Typeset a highly polished, two-page technical industry resume for a Principal Distributed Systems & Full-Stack Architect.

Document Requirements:
1. Document Setup:
   - Modern executive layout on A4 paper (#set page(paper: "a4", margin: (x: 2cm, y: 2cm))).
   - Header with Candidate Name, Professional Title ('Principal Distributed Systems Architect / VP of Engineering'), Contact Details, LinkedIn, GitHub, Location.
   - Clear visual hierarchy with section icons/dividers, clean tags, and structured layout.

2. Content Structure (Substantive, metric-driven accomplishments using the STAR method):
   - Professional Executive Summary (15+ years experience designing hyper-scale distributed cloud platforms, high-throughput microservices, and AI inference engines).
   - Core Competencies Matrix (Use Typst table or grid organizing skills: Languages: Rust, Go, Python, C++, TypeScript; Cloud & Distributed: Kubernetes, Docker, Terraform, AWS, GCP, eBPF; Storage & Streaming: PostgreSQL, Redis, Apache Kafka, ClickHouse, Cassandra; Architecture: High-Availability, Zero-Downtime Migrations, Microservices, Event-Driven).
   - Professional Work Experience (3 major high-impact roles):
     * Role 1: Principal Systems Architect at Tier-1 Cloud Enterprise (5 years): Led architecture of global low-latency data plane serving 8M QPS; reduced P99 latency by 72%; orchestrated multi-region Kubernetes migration saving $4.5M annual AWS infrastructure cost; managed 35 senior engineers.
     * Role 2: Staff Infrastructure Engineer at High-Growth Fintech Platform (4 years): Designed high-speed ACID transaction settlement pipeline handling $12B annual volume with zero data loss; attained 99.999% SLA; built real-time fraud detection engine in Go and Kafka.
     * Role 3: Senior Backend Engineer at Enterprise SaaS Company (4 years): Architected distributed microservices and asynchronous task execution queues.
   - Major Architecture Case Studies (2 detailed highlighted projects with technical design highlights, trade-offs, scale metrics, and business ROI).
   - Patents & Open Source Contributions (2 granted US Patents in distributed consensus; Creator & Maintainer of popular open-source Rust RPC framework with 4.5k GitHub stars).
   - Education & Certifications (M.S. in Computer Science, B.S. in Software Engineering, AWS Certified Solutions Architect Professional, CKA).

3. Length Constraint:
   - The compiled document MUST span EXACTLY 2 pages (or between 2 and 3 full pages, strictly at least 2 pages and at most 5 pages). Ensure extensive metric-rich bullet points, full system case studies, and comprehensive competencies.""",
        "semantic_checker": lambda code: bool(
            re.search(r'(?i)(resume|cv|简历|履历|architect|架构师)', code) and
            re.search(r'(?i)(experience|skills|工作经历|专业技能)', code) and
            re.search(r'(?i)(distributed|systems|cloud|kubernetes|分布式)', code) and
            len(code.splitlines()) >= 50
        ),
    },

    # =========================================================================
    # CATEGORY 4: 矩阵分析期末考试卷 (Final Exam Paper) - 1 Task
    # =========================================================================
    {
        "id": "C1_08",
        "category": "exam",
        "category_zh": "期末考试卷",
        "name": "University Final Exam Paper: Advanced Matrix Analysis",
        "name_zh": "大学期末考试卷：《高等矩阵分析与计算》研究生期末试卷及作答规范",
        "target_page_range": (2, 5),
        "prompt_task": """Typeset a formal, rigorous university final examination paper titled 'Graduate Course Examination: Advanced Matrix Analysis and Applications'.

Document Requirements:
1. Document Setup & Exam Formatting:
   - Formal exam layout on A4 paper (#set page(paper: "a4", margin: (x: 2cm, y: 2.2cm), header: [...], footer: [...])).
   - Official exam header: University Name, School of Mathematical Sciences & Computational Engineering, Academic Year & Semester, Course Name, Course Code, Examination Time (120 Minutes), Total Score (100 Points).
   - Student Identification Box: Full Name, Student ID, Major/Department, Examination Room, Desk Number.
   - Marker Scoring Table: A clean Typst table with columns for Question 1, 2, 3, 4, Total Score, Marker Signature, Reviewer Signature.
   - Examination Rules & Academic Honor Code Statement.

2. Exam Content & Sections (Provide complete mathematical problems with point allocations):
   - Part I: Multiple Choice Questions (5 questions, 4 points each, total 20 points):
     * Q1: Unitary equivalence and singular value invariants.
     * Q2: Induced matrix norms and matrix condition number properties.
     * Q3: Schur triangularization and normal matrix characterizations.
     * Q4: Positive definiteness criteria and Rayleigh quotient bounds.
     * Q5: Spectral radius vs matrix norm convergence condition $lim_{k -> oo} A^k = 0$.
   - Part II: Fill-in-the-Blank Questions (5 questions, 4 points each, total 20 points):
     * Q6: Computing Jordan canonical form and minimal polynomial for a given 3x3 matrix.
     * Q7: Frobenius norm calculation of a specific block matrix.
     * Q8: Spectral decomposition of a real symmetric rank-1 perturbation matrix.
     * Q9: Matrix exponential $e^(A t)$ for a 2x2 nilpotent block.
     * Q10: Moore-Penrose pseudo-inverse $A^+$ properties and minimum-norm least-squares solution.
   - Part III: Comprehensive Computational Problems (2 major problems, 15 points each, total 30 points):
     * Q11 (15 pts): Given an explicit 3x3 defective matrix A, compute its characteristic polynomial, find the generalized eigenvectors, construct the similarity transformation matrix P, and determine the Jordan canonical form J such that $P^(-1) A P = J$. (Provide designated ruled answer space / boxed work area).
     * Q12 (15 pts): For a rectangular 3x2 matrix A and vector b, derive the complete Singular Value Decomposition (SVD) $A = U Sigma V^T$, identify singular values and left/right singular vectors, and calculate the minimum-norm least squares solution $x = A^+ b$.
   - Part IV: Rigorous Mathematical Proofs (2 proof problems, 15 points each, total 30 points):
     * Q13 (15 pts): State and prove the Courant-Fischer Min-Max Theorem (or Rayleigh-Ritz theorem) for the eigenvalues of a Hermitian matrix.
     * Q14 (15 pts): State and prove the Gershgorin Circle Theorem. Apply it to an explicit 4x4 diagonally dominant matrix to prove non-singularity and determine eigenvalue bounds.

3. Length Constraint:
   - The compiled exam paper MUST span between 2 and 4 full pages (strictly at least 2 pages, at most 5 pages). Include proper spacing, question descriptions, options, answer boxes, and scoring criteria so the paper reads like an authentic, complete multi-page university exam.""",
        "semantic_checker": lambda code: bool(
            re.search(r'(?i)(exam|examination|test|试卷|考试)', code) and
            re.search(r'(?i)(matrix analysis|linear algebra|矩阵分析|矩阵)', code) and
            re.search(r'(?i)(score|points|分值|题)', code) and
            len(code.splitlines()) >= 50
        ),
    },

    # =========================================================================
    # CATEGORY 5: 商业报告 (Business Reports) - 2 Tasks
    # =========================================================================
    {
        "id": "C1_09",
        "category": "business_report",
        "category_zh": "商业报告",
        "name": "Business Feasibility Report: Enterprise GenAI Adoption & Investment Appraisal",
        "name_zh": "商业可行性报告：企业级生成式人工智能应用转型与商业投资可行性报告",
        "target_page_range": (2, 5),
        "prompt_task": """Typeset a high-level executive business feasibility and investment appraisal report in Typst titled 'Commercial Feasibility & Strategic Investment Appraisal: Enterprise Generative AI Adoption & Workflow Automation'.

Document Requirements:
1. Document Setup & Corporate Styling:
   - Professional executive report formatting on A4 paper (#set page(paper: "a4", margin: (x: 2.5cm, y: 2.5cm))).
   - Executive header banner with Company Advisory Branding, Date, Project Code, Confidentiality Label, and Authoring Committee.
   - Structured typography using callout highlight cards, metric boxes, and clean financial tables.

2. Content Structure (Comprehensive business case with quantitative models):
   - Executive Summary: Key strategic drivers, projected 3-year Net Present Value (NPV of $14.2M), Internal Rate of Return (IRR of 42%), and 11-month capital payback period.
   - Section 1: Strategic Context & Market Opportunity:
     * Enterprise operational challenges: manual knowledge retrieval latency, customer support overhead.
     * Market sizing & benchmarks: TAM/SAM/SOM growth, competitor GenAI adoption indices.
   - Section 2: Technical Architecture & Deployment Solution:
     * Detailed comparative analysis table: Multi-tenant Commercial APIs vs On-Premises Open-Weights Deployment (comparing Data Privacy, Latency, Compliance, Infrastructure CapEx, and Ongoing OpEx).
     * Proposed hybrid deployment architecture diagram/block.
   - Section 3: Financial Valuation & 3-Year Total Cost of Ownership (TCO) Model:
     * Full financial statement table detailing Year 1, Year 2, and Year 3 expenditures: GPU Cloud Compute, Model Fine-Tuning, Security/Compliance, Personnel Training.
     * Projected direct savings: 45% reduction in customer ticket resolution time, $5.8M annual operational labor redeployment, incremental cross-sell revenue.
   - Section 4: Implementation Phasing & Milestone Roadmap:
     * Structured quarterly roadmap table across 4 phases: Q1 Foundation & PoC, Q2 Departmental Pilot Launch, Q3 Cross-Enterprise Rollout, Q4 Autonomous Optimization.
   - Section 5: Comprehensive Enterprise Risk & Governance Matrix:
     * Structured risk matrix table evaluating 5 core enterprise risks: Data Privacy/IP Leakage, Hallucination/Safety, Regulatory Compliance (EU AI Act, GDPR), Vendor Lock-in, Change Management Friction; with Likelihood, Impact, and Mitigation Countermeasures.
   - Section 6: Steering Committee Strategic Recommendations & Actionable Next Steps.

3. Length Constraint:
   - The compiled document MUST span between 2 and 4 full pages (at least 2 pages, at most 5 pages). Provide rich textual analyses, detailed financial tables, strategic roadmaps, and actionable governance frameworks.""",
        "semantic_checker": lambda code: bool(
            re.search(r'(?i)(report|feasibility|business|报告|商业|可行性)', code) and
            re.search(r'(?i)(executive summary|roi|investment|投资|成本|收益)', code) and
            ('table(' in code or 'table.' in code or 'table' in code) and
            len(code.splitlines()) >= 50
        ),
    },

    {
        "id": "C1_10",
        "category": "business_report",
        "category_zh": "商业报告",
        "name": "Strategic Consulting Report: Supply Chain Modernization & Financial Operations",
        "name_zh": "商业战略咨询报告：科技企业年度数字化供应链优化与财务运营战略分析",
        "target_page_range": (2, 5),
        "prompt_task": """Typeset an executive strategic management consulting report in Typst titled 'Strategic Advisory Report: Operational Modernization and Digital Supply Chain Optimization for High-Tech Manufacturing'.

Document Requirements:
1. Document Setup & Corporate Design:
   - Polished management consulting layout on A4 paper (#set page(paper: "a4", margin: (x: 2.5cm, y: 2.5cm))).
   - Executive header, formal corporate styling, numbered sections, callout boxes for Key Insights and Executive Takeaways.

2. Content Structure (In-depth management consulting deliverable):
   - Executive Summary: Macro industry supply chain turbulence, core diagnostic findings, projected working capital release of $38.5M, and EBITDA margin improvement by 280 bps.
   - Section 1: Operational Diagnostic & Current State Assessment:
     * Root-cause breakdown of supply chain bottlenecks: lead-time volatility, component inventory obsolescence, bullwhip effect in multi-tier procurement.
   - Section 2: Executive KPI Dashboard & Performance Baseline:
     * Detailed multi-column comparative table: Metric Name, Current Company Baseline, Industry Top-Quartile Benchmark, Target Year 1, Target Year 3.
     * Metrics including: Days Inventory Outstanding (DIO), On-Time In-Full (OTIF) Delivery Rate, Cash-to-Cash Cycle Time, Supply Chain Cost % of Revenue, Supplier Fill Rate.
   - Section 3: Strategic Transformation Framework (Three Core Strategic Pillars):
     * Pillar 1: AI-Driven Demand Sensing & Predictive S&OP Forecasting.
     * Pillar 2: Dynamic Multi-Tier Supplier Control Tower & Resilient Dual-Sourcing Network.
     * Pillar 3: Automated Micro-Fulfillment & Smart Warehouse Integration.
   - Section 4: Financial Impact Model & Value Creation Projections:
     * Full financial projection table: Quantifying working capital release, freight cost reductions, inventory carrying cost savings, and net cash flow impact over a 3-year horizon.
   - Section 5: Organizational Change Management & Governance:
     * Steering committee governance model, agile cross-functional transformation squads, supplier KPI scorecard integration.
   - Section 6: Execution Roadmap & 100-Day Acceleration Plan:
     * Milestone action plan table dividing transformation initiatives into Days 1-30 (Rapid Diagnostics & Baseline), Days 31-60 (Pilot S&OP Launch), Days 61-100 (Full-Scale Wave 1 Integration).
   - Section 7: Conclusion & Immediate Decision Triggers for the Board of Directors.

3. Length Constraint:
   - The compiled document MUST span between 2 and 4 full pages (at least 2 pages, at most 5 pages). Provide exhaustive narrative analysis, multiple detailed tables, key metric callouts, and structured implementation frameworks.""",
        "semantic_checker": lambda code: bool(
            re.search(r'(?i)(supply chain|strategy|consulting|供应链|战略|咨询)', code) and
            re.search(r'(?i)(kpi|financial|dashboard|财务|运营)', code) and
            ('table(' in code or 'table.' in code or 'table' in code) and
            len(code.splitlines()) >= 50
        ),
    },
]

TASK_MAP = {t["id"]: t for t in TASKS}
