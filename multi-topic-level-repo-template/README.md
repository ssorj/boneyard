# Documentation Repository

WARNING: as of 18 August 2016, this template repo is still under heavy development! Email <dhensley@redhat.com> if you're interested in using it!

The multi-topic-level-repo-template is a Git repository template for multiple titles in a single repo that Silas and the Customer Platform team collaborate on in order to provide a flexible Git repository structure that works with the Docs2Drupal publication system, is topic-oriented, enables simple upstream-downstream collaboration, and in the future can allow for cross-repo content-sharing. The multi-topic-level-repo-template has the following properties:

* multiple titles in a single repository
* the repo structure makes it clear whether a topic is local to the specific distro of a title, shared between distros of a title, or shared between more than one titles
* because of the repo structure with different levels of topic-sharing, the need for file naming conventions is reduced
* it will work with a Github-first development model
* it should work with all other documentation development models
* it can easily be mirrored between Github and Gitlab using a script
* in the future, Silas and the Customer Platform team will be testing cross-repo content-sharing using this repo templates


You can review the [repository structure](#repository-structure), and [use this repository template](#use-this-repository-template) as a starting point for your project.

## Repository Structure Overview

This repository contains all of the documentation for XYZ product name. It uses the following directory structure:

~~~
├── books
│   ├── my-title-a
│   │   ├── product
│   │   │   ├── master.adoc
│   │   │   ├── master-docinfo.xml
│   │   │   ├── global -> ../../../global
│   │   │   └── local -> ../local
│   │   ├── local
│   │   │   ├── global -> ../../../global
│   │   │   ├── topic-1.adoc
│   │   │   ├── topic-2.adoc
│   │   │   ├── topic-4.adoc
│   │   │   ├── topic-5.adoc
│   │   │   ├── topic-6.adoc
│   │   │   └── topic-7.adoc
│   │   └── upstream-1
│   │       ├── master.adoc
│   │       ├── master-docinfo.xml
│   │       ├── master.html
│   │       ├── global -> ../../../global
│   │       └── local -> ../local
│   └── my-title-b
│        ├── product
│        │   ├── master.adoc
│        │   ├── master-docinfo.xml
│        │   ├── global -> ../../../global
│        │   └── local -> ../local
│        ├── local
│        │   ├── global -> ../../../global
│        │   ├── topic-1.adoc
│        │   ├── topic-2.adoc
│        │   ├── topic-4.adoc
│        │   ├── topic-5.adoc
│        │   ├── topic-6.adoc
│        │   └── topic-7.adoc
│        └── upstream-1
│           ├── master.adoc
│           ├── master-docinfo.xml
│           ├── master.html
│           ├── global -> ../../../global
│           └── local -> ../local
├── global
│   ├── document-attributes.adoc
│   ├── revision-info.adoc
│   ├── topic-shared-1.adoc
│   └── topic-shared-2.adoc
├── images
│   └── broccoli.png
├── internal
├── README.md
└── scripts — Contains scripts to automate the processes used to create and build documentation
    └── buildGuides.sh — Builds the top-level Guides that live in the docs/ folders
~~~

## Use this Repository Template

Clone this repository to your local machine. You may want to build the books in this example repository and review the output to understand how it works before you make any changes.

### Build the Example Books

To build all of the example books, open a terminal, navigate to the root directory of this repository, and type the following command:

        $ scripts/buildGuides.sh

The script provides links to both AsciiDoctor and ccutil builds for each of the example books. Look at the rendered HTML to see how the preprocessor directives work to conditionally display content.

You can also build a single guide. Navigate to the folder of the book you want to build and type the following command:

        $ ./buildGuide.sh

### Modify the Example Books for Your Documentation

Copy the structure into your own local repository and make the following changes to customize this template for your implementation.

1. Add your Asciidoc `*.adoc` files to the `topics/` folder.
2. Replace the values in the `docs/topics/document-attributes.adoc` file for your documentation.
  * Replace the product names and releases.
  * Replace the book names.
3. Use 'git mv' to rename the book folder names.

        $ cd My_Title_A
        $ git mv My_Title_A Installation_Guide.
4. In a terminal, navigate to each book folder and add the symlink to the `topics/` using this command:

        $ ln -s ../topics topics
5. Within each book folder, modify the `master-docinfo.xml` file to set the appropriate title, product, release, and other values for the build of the book to the portal.
6. Within each book folder, modify the `master.adoc` file to set the appropriate title, document attributes, and include the appropriate `topics/` content.
7. When you are ready, run the scripts to build the guides and review the output to make sure it looks correct.
