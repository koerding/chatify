import time

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, LLMMathChain

from .llm_models import ModelsFactory
from .cache import LLMCacher


class CreateLLMChain:
    """Class for creating and executing Language Model (LLM) chains."""

    def __init__(self, config):
        """Initializes the CreateLLMChain object.

        Parameters
        ----------
        config (dict): Configuration settings for the LLM chain.

        Returns
        -------
        None
        """
        self.chain_config = config['chain_config']
        self.llm_model = None
        self.cache = config['cache_config']['cache']
        self.llm_models_factory = ModelsFactory()
        self.cacher = LLMCacher(config)
        self._setup_chain_factory()
        return None

    def _setup_chain_factory(self):
        """Sets up the chain factory dictionary.

        Returns
        --------
        None
        """
        self.chain_factory = {'math': LLMMathChain, 'default': LLMChain}

    def create_prompt(self, prompt):
        """Creates a prompt using a template and input variables.

        Parameters
        ----------
        prompt (dict): Prompt configuration containing the template and input variables.

        Returns
        -------
        PROMPT (PromptTemplate): Prompt template object.
        """
        PROMPT = PromptTemplate(
            template=prompt['content'], input_variables=prompt['input_variables']
        )
        return PROMPT

    def create_chain(self, model_config, prompt_template):
        """Creates an LLM chain based on the model configuration and prompt template.

        Parameters
        ----------
        model_config (dict): Configuration settings for the LLM model.
        prompt_template (PromptTemplate): Prompt template object.

        Returns
        -------
        chain (LLMChain): LLM chain object.
        """
        if self.llm_model is None:
            self.llm_model = self.llm_models_factory.get_model(model_config)

            if self.cache:
                self.llm_model = self.cacher.cache_llm(self.llm_model)

        try:
            chain_type = self.chain_config['chain_type']
        except KeyError:
            chain_type = 'default'

        chain = self.chain_factory[chain_type](
            llm=self.llm_model, prompt=self.create_prompt(prompt_template)
        )
        return chain

    def execute(self, chain, inputs, *args, **kwargs):
        """Executes the LLM chain with the given inputs.

        Parameters
        ----------
        chain (LLMChain): LLM chain object.
        inputs (str): Input text to be processed by the chain.
        *args: Additional positional arguments.
        **kwargs: Additional keyword arguments.

        Returns
        -------
        output: Output text generated by the LLM chain.
        """
        if self.cache:
            inputs = chain.prompt.format(text=inputs)
            output = chain.llm(inputs, cache_obj=self.cacher.llm_cache)
            self.cacher.llm_cache.flush()
        else:
            output = chain(inputs)['text']

        return output
