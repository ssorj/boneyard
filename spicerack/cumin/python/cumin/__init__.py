# Doing this here is a problem, since subpieces of cumin like cumin.util or cumin.formats are
# widely used in other modules like mint or rosemary.  This causes everything to be touched
# when cumin.x is referenced, and it causes circular dependencies.

#from main import *
