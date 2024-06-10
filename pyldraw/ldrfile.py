from collections import Counter
from .geometry import Vector, Matrix
from .ldrobj import LdrObj

START_TOKENS = ["PLI BEGIN IGN", "BUFEXCHG STORE"]
END_TOKENS = ["PLI END", "BUFEXCHG RETRIEVE"]


def recursive_unwrap_model(
    model,
    submodels,
    objects=None,
    offset=None,
    matrix=None,
    only_submodel=None,
):
    """Recursively parses an LDraw model plus any submodels and
    populates an object list representing that model.  To support selective
    parsing of only one submodel, only_submodel can be set to the desired
    submodel name."""
    o = offset if offset is not None else Vector(0, 0, 0)
    m = matrix if matrix is not None else Matrix.identity()
    if objects is None:
        objects = []
    for obj in model:
        if only_submodel is not None:
            if not obj.is_model_named(only_submodel):
                continue
        if obj.model_name in submodels:
            submodel = submodels[obj.model_name]
            new_matrix = m * obj.matrix
            new_loc = m * obj.pos
            new_loc += o
            recursive_unwrap_model(
                submodel,
                submodels,
                objects,
                offset=new_loc,
                matrix=new_matrix,
            )
        else:
            if only_submodel is None:
                new_obj = obj.copy()
                new_obj = new_obj.transformed(matrix=m, offset=o)
                objects.append(new_obj)
    return objects


class LdrStep:
    """LdrStep is a simple container for LdrObj objects associated with s single step.
    LdrStep objects are delimited by STEP directives in an LDraw file.
    """

    def __init__(self, objs=None, **kwargs):
        self.objs = []
        if objs is not None:
            self.objs = objs
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v
        self._sub_models = None
        self._parts = None

    def __repr__(self) -> str:
        return "%s(%d objects)" % (self.__class__.__name__, len(self.objs))

    def iter_objs(self):
        for o in self.objs:
            yield o

    @property
    def sub_models(self):
        """Returns a dictionary of quantities of unique sub-model references in this step"""
        if self._sub_models is not None:
            return self._sub_models
        self._sub_models = Counter()
        for o in self.objs:
            if o.model_name is not None:
                self._sub_models.update([o.model_name])
        return self._sub_models

    @property
    def parts(self):
        """Returns a dictionary of quantities of unique part references in this step"""
        if self._parts is not None:
            return self._parts
        self._parts = Counter()
        for o in self.objs:
            if o.part_name is not None:
                self._parts.append([o.part_name])
        return self._parts


class BuildStep(LdrStep):
    """BuildStep is a richer representation of LdrStep with additional data to
    represent a building step in an instruction sequence. It also stores
    unwrapped object representations of the objects added at this step as well
    as the total model representation at this step."""

    def __init__(self, objs=None, **kwargs):
        super().__init__(objs, **kwargs)
        self.scale = 1
        self.aspect = Vector(0, 0, 0)
        self.pos = Vector(0, 0, 0)
        self.idx = None
        self.level = None
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v
        # container for all objects which represent the complete model at this step
        self._model_objs = None
        # container for all objects added at this step
        self._step_objs = None

    def __repr__(self) -> str:
        return "%s(%d step objects)" % (self.__class__.__name__, len(self.step_objs))

    def unwrap(self, sub_models, model_objs=None):
        self._step_objs = None
        objs = recursive_unwrap_model(self.objs, sub_models)
        self._step_objs = [o.rotated_by(self.aspect) for o in objs]
        if model_objs is not None:
            objs = recursive_unwrap_model(self.objs, sub_models, objects=model_objs)
            self._model_objs = [o.rotated_by(self.aspect) for o in objs]

    @property
    def step_objs(self):
        if self._step_objs is not None:
            return self._step_objs

    @property
    def model_objs(self):
        if self._model_objs is not None:
            return self._model_objs


class LdrModel:
    """LdrModel is a simple container for LdrSteps within a single model definition.
    LdrModel objects are delimited by FILE / NOFILE directives in the LDraw file."""

    def __init__(self, name, **kwargs):
        self.name = name
        self.steps = []

    def __repr__(self) -> str:
        return "%s(%s)" % (self.__class__.__name__, self.name)

    def iter_steps(self):
        for step in self.steps:
            yield step

    def iter_objs(self):
        for step in self.steps:
            for obj in step.iter_objs():
                yield obj

    def build_steps(self, sub_models, at_aspect=None):
        aspect = at_aspect if at_aspect is not None else Vector(0, 0, 0)
        steps = []
        for step in self.iter_steps():
            build_step = BuildStep(objs=step.objs, aspect=aspect)
            build_step.unwrap(sub_models)
            steps.append(build_step)
        return steps

    @staticmethod
    def from_str(s, name=None):
        objs = []
        steps = []
        for line in s.splitlines():
            obj = LdrObj.from_str(line)
            if obj is not None:
                objs.append(obj)
                if obj.is_step_delimiter:
                    steps.append(LdrStep(objs))
                    objs = []
        m = LdrModel()
        if name is not None:
            m.name = name
        else:
            if steps[0][0].is_model_name:
                m.name = steps[0][0].model_name
        m.steps = steps
        return m


class UnwrapCtx:
    def __init__(self, model_name, model, **kwargs):
        self.model_name = model_name
        self.model = model
        self.idx = 0
        self.level = 0
        self.qty = 0
        self.model_objs = []
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v


class LdrFile:
    """LdrFile is a simple container for objects parsed from an LDraw file.
    It stores a root model and a dictionary of sub-models; each of which are
    LdrModel objects.  After parsing, a list of building steps is computed
    which represent a recursively unwrapped sequence of building instructions."""

    def __init__(self, filename=None, **kwargs):
        self.filename = filename
        # root model
        self.root = None
        # dictionary of submodels
        self.models = {}
        # list of unwrapped building steps (BuildStep objects)
        self.build_steps = None
        if filename is not None:
            self.parse_file(filename)

    def __repr__(self) -> str:
        return "%s(%s)" % (self.__class__.__name__, self.filename)

    def parse_file(self, filename=None):
        filename = filename if filename is not None else self.filename
        self.models = {}
        with open(filename, "rt") as fp:
            models = fp.read().split("0 FILE")
            root = None
            if len(models) == 1:
                root = models[0]
            else:
                root = "0 FILE " + models[1]
                for model in models[2:]:
                    model_name = model.splitlines()[0].lower().strip()
                    model_str = "0 FILE " + model
                    m = LdrModel.from_str(model_str, model_name)
                    self.models[model_name] = m
            self.root = LdrModel.from_str(root, name="root")
        self.build_steps, _ = self.unwrap_build_steps()

    def unwrap_build_steps(self, ctx=None, unwrapped=None):
        if ctx is None:
            ctx = UnwrapCtx("root", self.root)
            unwrapped = []
        for step in ctx.model.build_steps(self.models):
            if len(step.sub_models) > 0:
                for name, qty in step.sub_models.items():
                    new_ctx = UnwrapCtx(
                        name,
                        self.models[name],
                        idx=ctx.idx + 1,
                        level=ctx.level + 1,
                        qty=qty,
                    )
                    _, new_idx = self.unwrap_build_steps(
                        ctx=new_ctx,
                        unwrapped=unwrapped,
                    )
                    ctx.idx = new_idx
            build_step = BuildStep(
                objs=step.objs,
                idx=ctx.idx,
                level=ctx.level,
                aspect=step.aspect,
            )
            build_step.unwrap(self.models, model_objs=ctx.model_objs)
            unwrapped.append(build_step)
            ctx.idx += 1
        return unwrapped, ctx.idx
