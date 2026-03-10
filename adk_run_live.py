  async def run_live(
      self,
      invocation_context: InvocationContext,
  ) -> AsyncGenerator[Event, None]:
    """Runs the flow using live api."""
    llm_request = LlmRequest()
    event_id = Event.new_id()

    # Preprocess before calling the LLM.
    async with Aclosing(
        self._preprocess_async(invocation_context, llm_request)
    ) as agen:
      async for event in agen:
        yield event
    if invocation_context.end_invocation:
      return

    llm = self.__get_llm(invocation_context)
    logger.debug(
        'Establishing live connection for agent: %s with llm request: %s',
        invocation_context.agent.name,
        llm_request,
    )

    attempt = 1
    while True:
      try:
        # On subsequent attempts, use the saved token to reconnect
        if invocation_context.live_session_resumption_handle:
          logger.info('Attempting to reconnect (Attempt %s)...', attempt)
          attempt += 1
          if not llm_request.live_connect_config:
            llm_request.live_connect_config = types.LiveConnectConfig()
          if not llm_request.live_connect_config.session_resumption:
            llm_request.live_connect_config.session_resumption = (
                types.SessionResumptionConfig()
            )
          llm_request.live_connect_config.session_resumption.handle = (
              invocation_context.live_session_resumption_handle
          )
          llm_request.live_connect_config.session_resumption.transparent = True

        logger.info(
            'Establishing live connection for agent: %s',
            invocation_context.agent.name,
        )
        async with llm.connect(llm_request) as llm_connection:
          if llm_request.contents:
            # Sends the conversation history to the model.
            with tracer.start_as_current_span('send_data'):
              # Combine regular contents with audio/transcription from session
              logger.debug('Sending history to model: %s', llm_request.contents)
              await llm_connection.send_history(llm_request.contents)
              trace_send_data(
                  invocation_context, event_id, llm_request.contents
              )

          send_task = asyncio.create_task(
              self._send_to_model(llm_connection, invocation_context)
          )

          try:
            async with Aclosing(
                self._receive_from_model(
                    llm_connection,
                    event_id,
                    invocation_context,
                    llm_request,
                )
            ) as agen:
              async for event in agen:
                # Empty event means the queue is closed.
                if not event:
                  break
                logger.debug('Receive new event: %s', event)
                yield event
                # send back the function response to models
                if event.get_function_responses():
                  logger.debug(
                      'Sending back last function response event: %s', event
                  )
                  invocation_context.live_request_queue.send_content(
                      event.content
                  )
                # We handle agent transfer here in `run_live` rather than
                # in `_postprocess_live` to prevent duplication of function
                # response processing. If agent transfer were handled in
                # `_postprocess_live`, events yielded from child agent's
                # `run_live` would bubble up to parent agent's `run_live`,
                # causing `event.get_function_responses()` to be true in both
                # child and parent, and `send_content()` to be called twice for
                # the same function response. By handling agent transfer here,
                # we ensure that only child agent processes its own function
                # responses after the transfer.
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].function_response
                    and event.content.parts[0].function_response.name
                    == 'transfer_to_agent'
                ):
                  await asyncio.sleep(DEFAULT_TRANSFER_AGENT_DELAY)
                  # cancel the tasks that belongs to the closed connection.
                  send_task.cancel()
                  logger.debug('Closing live connection')
                  await llm_connection.close()
                  logger.debug('Live connection closed.')
                  # transfer to the sub agent.
                  transfer_to_agent = event.actions.transfer_to_agent
                  if transfer_to_agent:
                    logger.debug('Transferring to agent: %s', transfer_to_agent)
                    agent_to_run = self._get_agent_to_run(
                        invocation_context, transfer_to_agent
                    )
                    async with Aclosing(
                        agent_to_run.run_live(invocation_context)
                    ) as agen:
                      async for item in agen:
                        yield item
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].function_response
                    and event.content.parts[0].function_response.name
                    == 'task_completed'
                ):
                  # this is used for sequential agent to signal the end of the agent.
                  await asyncio.sleep(DEFAULT_TASK_COMPLETION_DELAY)
                  # cancel the tasks that belongs to the closed connection.
                  send_task.cancel()
                  return
          finally:
            # Clean up
            if not send_task.done():
              send_task.cancel()
            try:
              await send_task
            except asyncio.CancelledError:
              pass
      except (ConnectionClosed, ConnectionClosedOK) as e:
        # when the session timeout, it will just close and not throw exception.
        # so this is for bad cases
        logger.error('Connection closed: %s.', e)
        raise
      except Exception as e:
        logger.error(
            'An unexpected error occurred in live flow: %s', e, exc_info=True
        )
        raise

